TYPES = UNKNOWN_UC, GENERIC_UC, MOTION_UC, ARM_UC = range(4)

ORDERS = IDENTIFY, RAW_MOVE, GET_VAR, SET_VAR, ARC, TRACK_ERROR, _, _, _, _, _, _, _, _, _, _ = range(16)
ORDER_NAMES = 'IDE RAW GET SET ARC TRA ___ ___ ___ ___ ___ ___ ___ ___ ___ ___'.split()
ORDER_TARGETS = (
    GENERIC_UC, MOTION_UC, GENERIC_UC, GENERIC_UC, MOTION_UC
)


VARIABLES = DIST_KP, DIST_KI, DIST_KD, DIR_KP, DIR_KI, DIR_KD, K_ALI, MOTION_SPEED, ACCELERATION = range(9)
VARIABLE_NAMES = 'distKp distKi distKd dirKp dirKi dirKd Kali motion_speed acceleration'.split()

FEEDBACKS = ACK, IDE, TER, VAR, TRA, _, _, _, _, _, _, _, _, _, _, _ = range(16)
FEEDBACK_NAMES = 'ACK IDE TER VAR TRA ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___'.split()
FEEDBACK_CALLBACKS = 'acknowledge identify terminate variable track_error'.split()
