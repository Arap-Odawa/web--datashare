function add_tag_to_record(tag, timestamp, record)
    -- Inject the actual Fluent Bit tag into the record payload
    new_record = record
    new_record["container_tag"] = tag
    
    -- Return code 2 means the record was modified; 
    -- also return the timestamp and the updated record
    return 2, timestamp, new_record
end