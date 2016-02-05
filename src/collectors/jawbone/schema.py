'''
Created on Sep 10, 2015

@author: kevinchien
'''

SCHEMA_RET_META = {
    "type" : "object",
    "properties": {
        "user_xid" : {"type" : "string", "minLength" : 16, "maxLength" : 50},
        "code" : {"type" : "integer", "minimum" : 0, "maximum" : 100000},
        "time" : {"type" : "integer", "minimum" : 0, "maximum" : 9999999999}
    },
    "required": {"code", "user_xid", "time"}
}

SCHEMA_BAND_EVENT_ITEM =  {
    "type" : "array",
    "properties": {
        "date" : {"type" : "integer", "minimum" : 0, "maximum" : 20200000},
        "action" : {"type" : "string", "minLength" : 1, "maxLength" : 128},
        "tz" : {"type" : "string", "minLength" : 1, "maxLength" : 128},
        "time_created" : {"type" : "integer", "minimum" : 0, "maximum" : 9999999999},
        "required": {"date", "action", "time_created", "tz"}
    }
}

SCHEMA_BANDS_EVENTS_DATA = {
    "type" : "object",
    "properties": {
       "items" : SCHEMA_BAND_EVENT_ITEM,
    }
}

SCHEMA_BAND_EVENTS = {
    "type" : "object",
    "properties": {
        "meta": SCHEMA_RET_META,
        "data": SCHEMA_BANDS_EVENTS_DATA,
    },
    "required": {"meta"}
}

SCHEMA_BODY_EVENT_ITEM =  {
    "type" : "array",
    "properties": {
        "date" : {"type" : "integer", "minimum" : 0, "maximum" : 20200000},
        "time_created" : {"type" : "integer", "minimum" : 0, "maximum" : 9999999999},
        "time_updated" : {"type" : "integer", "minimum" : 0, "maximum" : 9999999999},        
        "place_name" : {"type" : "string", "minLength" : 1, "maxLength" : 64},
        "place_lat" : {"type" : "string", "minLength" : 1, "maxLength" : 32},
        "place_lon" : {"type" : "string", "minLength" : 1, "maxLength" : 32},
        "place_acc" : {"type" : "integer", "minimum" : 0, "maximum" : 9999},
        "lean_mass" : {"type" : "integer", "minimum" : 0, "maximum" : 9999},
        "weight" : {"type" : "integer", "minimum" : 0, "maximum" : 999},
        "body_fat" : {"type" : "integer", "minimum" : 0, "maximum" : 100},
        "bmi" : {"type" : "integer", "minimum" : 0, "maximum" : 999},                
    }
}

SCHEMA_BODY_EVENTS_DATA = {
    "type" : "object",
    "properties": {
       "items" : SCHEMA_BODY_EVENT_ITEM,
    }
}

SCHEMA_BAND_EVENTS = {
    "type" : "object",
    "properties": {
        "meta": SCHEMA_RET_META,
        "data": SCHEMA_BODY_EVENTS_DATA,
    },
    "required": {"meta"}
}

SCHEMA_USER_PROFILE_DATA = {
    "type" : "object",
    "properties": {
        "xid" : {"type" : "string", "minLength" : 16, "maxLength" : 50},
        "last" : {"type" : "string", "minLength" : 16, "maxLength" : 50},
        "first" : {"type" : "string", "minLength" : 16, "maxLength" : 50},
        "weight" : {"type" : "integer", "minimum" : 0, "maximum" : 999},
        "height" : {"type" : "integer", "minimum" : 0, "maximum" : 999},
    },
    "required": {"code", "user_xid", "time"}
}

SCHEMA_USER_PROFILE = {
    "type" : "object",
    "properties": {
        "meta": SCHEMA_RET_META,
        "data": SCHEMA_USER_PROFILE_DATA,
    },
    "required": {"meta"}
}

SCHEMA_USER_TRENDS = {
    "type" : "object",
    "properties": {
        "meta": SCHEMA_RET_META,
        "data": {}
    },
    "required": {"meta"}
}