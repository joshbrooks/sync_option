import { describe, test, expect, vi, beforeEach } from 'vitest';

// Import from the UMD module
const { GraphModel, Node, Edge } = require('./models');

// Mock the DB module that our GraphModel uses
const mockDB = {
    getData: vi.fn()
};
global.DB = mockDB;

describe('GraphModel', () => {
    let graph;

    beforeEach(() => {
        // Clear all mocks before each test
        vi.clearAllMocks();
        
        // Create new graph instance
        graph = new GraphModel();
        
        // Setup mock data
        mockDB.getData.mockImplementation(async (url) => {
            if (url === '/api/sync-option/options/groups') {
                return [
                    { name: 'sector', names: { en: 'Sectors', tet: 'Setór' } },
                    { name: 'subsector', names: { en: 'Subsectors', tet: 'Subsetór' } }
                ];
            }
            if (url === '/api/sync-option/options/groups/sector') {
                return [
                    
                        {
                            value: "1",
                            value_type: "integer",
                            names: { en: "Health", tet: "Saude" },
                            is_active: true,
                            sync_id: "01965400-bf6e-76f3-939f-1733e3c1f85d"
                        }
                    ]
                
            }
            if (url === '/api/sync-option/options/groups/subsector') {
                return [
                        {
                            value: "1",
                            value_type: "integer",
                            names: { en: "Building (Health)", tet: "Edifísiu (Saude)" },
                            is_active: true,
                            sync_id: "01965400-c109-79b2-b5c3-42298b09b670"
                        }
                    ]
            }
            if (url === '/api/sync-option/options/relations/sector') {
                return [
                    {
                        from_node: "42298b09b670",
                        from_group: "subsector",
                        to_node: "1733e3c1f85d",
                        to_group: "sector",
                        name: "belongs_to",
                        sync_id: "01965c05-505a-7533-ace6-1518a369ce4b"
                    }
                ];
            }
            return null;
        });
    });

    describe('Node and Edge Management', () => {
        test('should create empty graph', () => {
            expect(graph.nodes.size).toBe(0);
            expect(graph.edges.size).toBe(0);
            expect(graph.groupNodes.size).toBe(0);
    });

        test('should add and retrieve nodes', () => {
            const node = graph.addNode('test-id', 'test-group', { value: 'test' });
            
            expect(node).toBeInstanceOf(Node);
            expect(graph.nodes.size).toBe(1);
            expect(graph.groupNodes.get('test-group').size).toBe(1);
            
            const nodes = graph.getNodesInGroup('test-group');
        expect(nodes).toHaveLength(1);
            expect(nodes[0].data.value).toBe('test');
        });

        test('should add and retrieve edges', () => {
            // Add nodes first
            graph.addNode('node1', 'group1', { value: '1' });
            graph.addNode('node2', 'group2', { value: '2' });
            
            // Add edge
            const edge = graph.addEdge('node1', 'node2', 'test-relation');
            
            expect(edge).toBeInstanceOf(Edge);
            expect(graph.edges.size).toBe(1);
            
            // Test edge retrieval
            const outEdges = graph.getOutgoingEdges('node1');
            const inEdges = graph.getIncomingEdges('node2');
            
            expect(outEdges).toHaveLength(1);
            expect(inEdges).toHaveLength(1);
            expect(outEdges[0].fromNode).toBe('node1');
            expect(outEdges[0].toNode).toBe('node2');
    });

        test('should clear graph', () => {
            // Add some data
            graph.addNode('node1', 'group1', { value: '1' });
            graph.addNode('node2', 'group2', { value: '2' });
            graph.addEdge('node1', 'node2', 'test-relation');
            
            // Clear graph
            graph.clear();

            expect(graph.nodes.size).toBe(0);
            expect(graph.edges.size).toBe(0);
            expect(graph.groupNodes.size).toBe(0);
        });
    });

    describe('Data Loading', () => {
        test('should load nodes from a group', async () => {
            const nodes = await graph.loadGroupNodes('sector');
            
            expect(nodes).toHaveLength(1);
            expect(graph.nodes.size).toBe(1);
            expect(graph.groupNodes.get('sector').size).toBe(1);
            
            const sectorNodes = graph.getNodesInGroup('sector');
            expect(sectorNodes[0].data.names.en).toBe('Health');
        });

        test('should load all nodes', async () => {
            const results = await graph.loadAllNodes();
            
            expect(results.size).toBe(2); // sector and subsector
            expect(graph.nodes.size).toBe(2);
            expect(graph.groupNodes.size).toBe(2);
    });

        test('should load relations for a group', async () => {
            // Load nodes first
            await graph.loadGroupNodes('sector');
            await graph.loadGroupNodes('subsector');
            
            // Load relations
            const edges = await graph.loadGroupRelations('sector');

            expect(edges).toHaveLength(1);
            expect(graph.edges.size).toBe(1);
        
            // Check edge properties
            const edge = graph.getOutgoingEdges('42298b09b670')[0];
            expect(edge.type).toBe('belongs_to');
            expect(edge.toNode).toBe('1733e3c1f85d');
        });

        test('should load all relations', async () => {
            // Load all nodes first
            await graph.loadAllNodes();

            // Load all relations
            const edges = await graph.loadAllRelations();
            
            expect(edges).toHaveLength(1);
            expect(graph.edges.size).toBe(1);
    });

    test('should handle missing data gracefully', async () => {
        // Mock DB to return null
        mockDB.getData.mockResolvedValue(null);
        
            const nodes = await graph.loadGroupNodes('nonexistent');
        expect(nodes).toHaveLength(0);

            const edges = await graph.loadGroupRelations('nonexistent');
            expect(edges).toHaveLength(0);
        });
    });

    describe('Graph Queries', () => {
        beforeEach(async () => {
            // Load test data
            await graph.loadAllNodes();
            await graph.loadAllRelations();
    });

        test('should get nodes by group', () => {
            const sectorNodes = graph.getNodesInGroup('sector');
            const subsectorNodes = graph.getNodesInGroup('subsector');
            
            expect(sectorNodes).toHaveLength(1);
            expect(subsectorNodes).toHaveLength(1);
            expect(sectorNodes[0].data.names.en).toBe('Health');
            expect(subsectorNodes[0].data.names.en).toBe('Building (Health)');
    });

        test('should get edges by node', () => {
            const outEdges = graph.getOutgoingEdges('42298b09b670');
            const inEdges = graph.getIncomingEdges('1733e3c1f85d');
            
            expect(outEdges).toHaveLength(1);
            expect(inEdges).toHaveLength(1);
            expect(outEdges[0].type).toBe('belongs_to');
            expect(inEdges[0].fromNode).toBe('42298b09b670');
        });
    });
}); 