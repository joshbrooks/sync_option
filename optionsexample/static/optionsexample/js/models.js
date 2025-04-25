// API endpoint configuration
const API_CONFIG = {
    BASE_PATH: '/api/sync-option',
    ENDPOINTS: {
        GROUPS: '/options/groups',
        GROUP_OPTIONS: (groupName) => `/options/groups/${groupName}`,
        GROUP_RELATIONS: '/options/grouprelations/',
        GROUP_RELATIONS_SPECIFIC: (groupName) => `/options/relations/${groupName}`
    }
};

/**
 * Represents a relationship type between option groups
 */
class RelationType {
    constructor(name, fromGroup, toGroup, fromMany, toMany, names = {}, descriptions = {}, syncId = null) {
        this.name = name;
        this.fromGroup = fromGroup;
        this.toGroup = toGroup;
        this.fromMany = fromMany;
        this.toMany = toMany;
        this.names = names;
        this.descriptions = descriptions;
        this.syncId = syncId;
    }

    /**
     * Get the cardinality description of this relationship
     * @returns {string} Description like 'many-to-one', 'one-to-many', etc.
     */
    get cardinality() {
        return `${this.fromMany ? 'many' : 'one'}-to-${this.toMany ? 'many' : 'one'}`;
    }

    /**
     * Check if this relationship type applies to the given groups
     * @param {string} fromGroupName - Name of the source group
     * @param {string} toGroupName - Name of the target group
     * @returns {boolean} Whether this relationship type applies
     */
    appliesTo(fromGroupName, toGroupName) {
        return this.fromGroup === fromGroupName && this.toGroup === toGroupName;
    }
}

/**
 * Represents a relationship between two options
 */
class Relation {
    constructor(fromOption, toOption, relationType, metadata = {}) {
        this.fromOption = fromOption;
        this.toOption = toOption;
        this.relationType = relationType;
        this.metadata = metadata;
    }
}

/**
 * Represents a node in the graph
 */
class Node {
    constructor(id, group, data) {
        this.id = id;
        this.group = group;
        this.data = data;
    }
}

/**
 * Represents an edge in the graph
 */
class Edge {
    constructor(fromNode, toNode, type, metadata = {}, syncId = null) {
        this.fromNode = fromNode;
        this.toNode = toNode;
        this.type = type;
        this.metadata = metadata;
        this.syncId = syncId;
    }
}

/**
 * Base class for interacting with cached graph data from IndexedDB
 */
class GraphModel {
    constructor() {
        this.nodes = new Map(); // Map<nodeId, Node>
        this.edges = new Map(); // Map<fromNode, Map<toNode, Edge>>
        this.groupNodes = new Map(); // Map<groupName, Set<nodeId>>
    }

    /**
     * Add a node to the graph
     * @param {string} id - Node ID
     * @param {string} group - Group name
     * @param {Object} data - Node data
     * @returns {Node} The added node
     */
    addNode(id, group, data) {
        const node = new Node(id, group, data);
        this.nodes.set(id, node);
        
        // Add to group index
        if (!this.groupNodes.has(group)) {
            this.groupNodes.set(group, new Set());
        }
        this.groupNodes.get(group).add(id);
        
        return node;
    }

    /**
     * Add an edge to the graph
     * @param {string} fromNode - Source node ID
     * @param {string} toNode - Target node ID
     * @param {string} type - Edge type
     * @param {Object} metadata - Edge metadata
     * @param {string} syncId - Sync ID
     * @returns {Edge} The added edge
     */
    addEdge(fromNode, toNode, type, metadata = {}, syncId = null) {
        if (!this.nodes.has(fromNode) || !this.nodes.has(toNode)) {
            throw new Error('Both nodes must exist in the graph before adding an edge');
        }

        const edge = new Edge(fromNode, toNode, type, metadata, syncId);
        
        // Add to adjacency list
        if (!this.edges.has(fromNode)) {
            this.edges.set(fromNode, new Map());
        }
        this.edges.get(fromNode).set(toNode, edge);
        
        return edge;
    }

    /**
     * Load nodes from a specific group into the graph
     * @param {string} groupName - Name of the group to load
     * @returns {Promise<Array<Node>>} Loaded nodes
     */
    async loadGroupNodes(groupName) {
        try {
            const endpoint = `${API_CONFIG.BASE_PATH}${API_CONFIG.ENDPOINTS.GROUP_OPTIONS(groupName)}`;
            const data = await DB.getData(endpoint);
            
            if (!data || !Array.isArray(data)) {
                console.warn(`No options found for group ${groupName}`);
                return [];
            }

            const nodes = data
                .filter(option => option.is_active)
                .map(option => {
                    const id = option.sync_id.slice(-12); // Last 12 chars of sync_id
                    return this.addNode(id, groupName, {
                        value: option.value,
                        valueType: option.value_type,
                        names: option.names || {},
                        descriptions: option.descriptions || {},
                        syncId: option.sync_id,
                        isActive: option.is_active
                    });
                });

            return nodes;
        } catch (error) {
            console.error(`Error loading nodes for group ${groupName}:`, error);
            return [];
        }
    }

    /**
     * Load all available groups and their nodes into the graph
     * @returns {Promise<Map<string, Array<Node>>>} Map of group names to their nodes
     */
    async loadAllNodes() {
        try {
            // First get all groups
            const groupsEndpoint = `${API_CONFIG.BASE_PATH}${API_CONFIG.ENDPOINTS.GROUPS}`;
            const groupsData = await DB.getData(groupsEndpoint);
            
            if (!groupsData || !Array.isArray(groupsData)) {
                console.warn('No groups found');
                return new Map();
            }

            // Load nodes for each group
            const results = new Map();
            for (const group of groupsData) {
                const nodes = await this.loadGroupNodes(group.name);
                results.set(group.name, nodes);
            }

            return results;
        } catch (error) {
            console.error('Error loading all nodes:', error);
            return new Map();
        }
    }

    /**
     * Load relations for a specific group into the graph
     * @param {string} groupName - Name of the group to load relations for
     * @returns {Promise<Array<Edge>>} Loaded edges
     */
    async loadGroupRelations(groupName) {
        try {
            const endpoint = `${API_CONFIG.BASE_PATH}${API_CONFIG.ENDPOINTS.GROUP_RELATIONS_SPECIFIC(groupName)}`;
            const relations = await DB.getData(endpoint);

            if (!relations || !Array.isArray(relations)) {
                console.warn(`No relations found for group ${groupName}`);
                return [];
            }

            const edges = relations.map(rel => {
                const fromId = rel.from_node;
                const toId = rel.to_node;
                
                // Ensure both nodes exist
                if (!this.nodes.has(fromId)) {
                    this.addNode(fromId, rel.from_group, { syncId: rel.from_node });
                }
                if (!this.nodes.has(toId)) {
                    this.addNode(toId, rel.to_group, { syncId: rel.to_node });
                }

                return this.addEdge(
                    fromId,
                    toId,
                    rel.name,
                    rel.metadata || {},
                    rel.sync_id
                );
            });

            return edges;
        } catch (error) {
            console.error(`Error loading relations for group ${groupName}:`, error);
            return [];
        }
    }

    /**
     * Load all relations from all groups into the graph
     * @returns {Promise<Array<Edge>>} All loaded edges
     */
    async loadAllRelations() {
        try {
            // First get all groups
            const groupsEndpoint = `${API_CONFIG.BASE_PATH}${API_CONFIG.ENDPOINTS.GROUPS}`;
            const groupsData = await DB.getData(groupsEndpoint);
            
            if (!groupsData || !Array.isArray(groupsData)) {
                console.warn('No groups found');
                return [];
            }

            // Load relations for each group
            const allEdges = [];
            for (const group of groupsData) {
                const edges = await this.loadGroupRelations(group.name);
                allEdges.push(...edges);
            }

            return allEdges;
        } catch (error) {
            console.error('Error loading all relations:', error);
            return [];
        }
    }

    /**
     * Get all nodes in a specific group
     * @param {string} groupName - Name of the group
     * @returns {Array<Node>} Nodes in the group
     */
    getNodesInGroup(groupName) {
        const nodeIds = this.groupNodes.get(groupName) || new Set();
        return Array.from(nodeIds).map(id => this.nodes.get(id)).filter(Boolean);
    }

    /**
     * Get all outgoing edges from a node
     * @param {string} nodeId - Source node ID
     * @returns {Array<Edge>} Outgoing edges
     */
    getOutgoingEdges(nodeId) {
        const edgeMap = this.edges.get(nodeId);
        return edgeMap ? Array.from(edgeMap.values()) : [];
    }

    /**
     * Get all incoming edges to a node
     * @param {string} nodeId - Target node ID
     * @returns {Array<Edge>} Incoming edges
     */
    getIncomingEdges(nodeId) {
        const incomingEdges = [];
        for (const [fromId, edgeMap] of this.edges) {
            const edge = edgeMap.get(nodeId);
            if (edge) {
                incomingEdges.push(edge);
            }
        }
        return incomingEdges;
    }

    /**
     * Get related nodes filtered by type
     * @param {string} nodeId - Source node ID
     * @param {Object} options - Filter options
     * @param {string} [options.toNodeType] - Filter by target node group/type
     * @param {string} [options.edgeType] - Filter by edge type
     * @returns {Array<Node>} Related nodes matching the filter criteria
     */
    getRelatedNodes(nodeId, options = {}) {
        const outgoingEdges = this.getOutgoingEdges(nodeId);
        
        // Filter edges based on criteria
        const filteredEdges = outgoingEdges.filter(edge => {
            const toNode = this.nodes.get(edge.toNode);
            
            // Skip if target node doesn't exist
            if (!toNode) return false;
            
            // Filter by node type if specified
            if (options.toNodeType && toNode.group !== options.toNodeType) {
                return false;
            }
            
            // Filter by edge type if specified
            if (options.edgeType && edge.type !== options.edgeType) {
                return false;
            }
            
            return true;
        });
        
        // Get the target nodes from filtered edges
        return filteredEdges.map(edge => this.nodes.get(edge.toNode));
    }

    /**
     * Get related nodes from incoming edges filtered by type
     * @param {string} nodeId - Target node ID
     * @param {Object} options - Filter options
     * @param {string} [options.fromNodeType] - Filter by source node group/type
     * @param {string} [options.edgeType] - Filter by edge type
     * @returns {Array<Node>} Related nodes matching the filter criteria
     */
    getRelatedNodesIncoming(nodeId, options = {}) {
        const incomingEdges = this.getIncomingEdges(nodeId);
        
        // Filter edges based on criteria
        const filteredEdges = incomingEdges.filter(edge => {
            const fromNode = this.nodes.get(edge.fromNode);
            
            // Skip if source node doesn't exist
            if (!fromNode) return false;
            
            // Filter by node type if specified
            if (options.fromNodeType && fromNode.group !== options.fromNodeType) {
                return false;
            }
            
            // Filter by edge type if specified
            if (options.edgeType && edge.type !== options.edgeType) {
                return false;
            }
            
            return true;
        });
        
        // Get the source nodes from filtered edges
        return filteredEdges.map(edge => this.nodes.get(edge.fromNode));
    }

    /**
     * Get all related nodes (both incoming and outgoing) filtered by type
     * @param {string} nodeId - Node ID
     * @param {Object} options - Filter options
     * @param {string} [options.nodeType] - Filter by related node group/type (applies to both directions)
     * @param {string} [options.edgeType] - Filter by edge type
     * @param {boolean} [options.incoming=true] - Include incoming relations
     * @param {boolean} [options.outgoing=true] - Include outgoing relations
     * @returns {Array<Node>} Related nodes matching the filter criteria
     */
    getRelatedNodesAll(nodeId, options = {}) {
        const { 
            nodeType,
            edgeType,
            incoming = true,
            outgoing = true
        } = options;

        const relatedNodes = new Set();

        if (outgoing) {
            const outgoingNodes = this.getRelatedNodes(nodeId, {
                toNodeType: nodeType,
                edgeType
            });
            outgoingNodes.forEach(node => relatedNodes.add(node));
        }

        if (incoming) {
            const incomingNodes = this.getRelatedNodesIncoming(nodeId, {
                fromNodeType: nodeType,
                edgeType
            });
            incomingNodes.forEach(node => relatedNodes.add(node));
        }

        return Array.from(relatedNodes);
    }

    /**
     * Clear the graph
     */
    clear() {
        this.nodes.clear();
        this.edges.clear();
        this.groupNodes.clear();
    }
}

// Export the classes and configuration
export { GraphModel, Node, Edge, RelationType, Relation, API_CONFIG }; 