from config import defaults

MEMORY_LIMIT      = 2**20*100
HEADERS_LENGTH    = 2**10*64
USER_LENGTH       = 28
READ_CHUNK_SIZE   = 2**10*64
PUBLIC_KEY_LENGTH = 96
KEY_LENGTH        = 32

INIT_PATH         = "data"
USER_DATA         = "pubkeys"
SERVER_DATA       = "servkeys"

RECV_TIMEOUT      = 120

USER_SERVER       = "utesla"
ADMIN_SERVICE     = "admin"
INDEX_NAME        = "index"
END_CHUNK         = defaults.end_chunk
SERVICE_FILE      = "services/"
