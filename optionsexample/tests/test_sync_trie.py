from datetime import datetime, timezone
import pytest
from optionsexample.sync_trie import LastUpdatedTrie, Option

def test_build_trie():
    # Test data
    options = [
        Option(group="group1", value="value1", last_updated=datetime(2024, 4, 15, 10, 30, 0, tzinfo=timezone.utc)),
        Option(group="group1", value="value2", last_updated=datetime(2024, 4, 15, 11, 30, 0, tzinfo=timezone.utc)),
        Option(group="group1", value="value3", last_updated=datetime(2024, 4, 16, 10, 30, 0, tzinfo=timezone.utc))
    ]

    # Build trie
    trie = LastUpdatedTrie(options)
    
    # Verify structure
    assert "2024" in trie.trie
    assert "4" in trie.trie["2024"]
    assert "15" in trie.trie["2024"]["4"]
    assert "10" in trie.trie["2024"]["4"]["15"]
    assert "30" in trie.trie["2024"]["4"]["15"]["10"]
    assert "0" in trie.trie["2024"]["4"]["15"]["10"]["30"]
    assert trie.trie["2024"]["4"]["15"]["10"]["30"]["0"]["count"] == 1

def test_find_missing_objects():
    # Test data with duplicate timestamps
    timestamp1 = datetime(2024, 4, 15, 10, 30, 0, tzinfo=timezone.utc)
    timestamp2 = datetime(2024, 4, 15, 11, 30, 0, tzinfo=timezone.utc)
    timestamp3 = datetime(2024, 4, 16, 10, 30, 0, tzinfo=timezone.utc)

    all_options = [
        Option(group="group1", value="value1", last_updated=timestamp1),
        Option(group="group1", value="value2", last_updated=timestamp1),  # Duplicate timestamp
        Option(group="group1", value="value3", last_updated=timestamp2),
        Option(group="group1", value="value4", last_updated=timestamp3)
    ]

    # Create trie with only some objects
    partial_options = [all_options[0], all_options[2]]  # First 10:30 and 11:30
    trie = LastUpdatedTrie(partial_options)

    # Find missing objects
    missing = trie.find_missing_objects(all_options)
    
    # Should find 3 missing objects (one duplicate 10:30 and the 16th)
    assert len(missing) == 3
    
    # Verify the duplicate timestamp is included
    objects_with_duplicate = [obj for obj in missing if obj.last_updated == timestamp1]
    assert len(objects_with_duplicate) == 1

    # Verify all expected timestamps are present
    missing_timestamps = [obj.last_updated for obj in missing]
    assert timestamp1 in missing_timestamps
    assert timestamp3 in missing_timestamps

def test_empty_trie():
    trie = LastUpdatedTrie()
    assert trie.trie == {}
    
    # Test with empty list
    trie = LastUpdatedTrie([])
    assert trie.trie == {}

def test_invalid_timestamps():
    # Test with invalid timestamp
    with pytest.raises(ValueError):
        options = [Option(group="group1", value="value1", last_updated="invalid-timestamp")]
        LastUpdatedTrie(options)

def test_debug_trie(capsys):
    # Test data
    options = [
        Option(group="group1", value="value1", last_updated=datetime(2024, 4, 15, 10, 30, 0, tzinfo=timezone.utc)),
        Option(group="group1", value="value2", last_updated=datetime(2024, 4, 15, 11, 30, 0, tzinfo=timezone.utc))
    ]

    # Build trie and debug
    trie = LastUpdatedTrie(options)
    trie.debug_trie()
    
    # Capture output
    captured = capsys.readouterr()
    output = captured.out
    
    # Verify debug output contains expected structure
    assert "2024" in output
    assert "4" in output
    assert "15" in output
    assert "10" in output
    assert "11" in output
    assert "30" in output
    assert "count" in output 