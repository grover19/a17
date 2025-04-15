import data.manuscripts.fields as flds

# states:
AUTHOR_REV = 'AUR'
COPY_EDIT = 'CED'
IN_REF_REV = 'REV'
REJECTED = 'REJ'
SUBMITTED = 'SUB'
WITHDRAWN = 'WIT'
AUTHOR_REVISIONS = 'AUTHREVISION'
ACCWITHREV = "ACCWITHREV"
EDITOR_REVIEW = 'EDREV'
FORMATTING = 'FORM'
PUBLISHED = 'PUB'
TEST_STATE = SUBMITTED

STATE_NAME_TO_CODE = {
    "Submitted": "SUB",
    "Referee Review": "REV",
    "Copy Edit": "CED",
    "Author Revisions": "AUTHREVISION",
    "Editor Review": "EDREV",
    "AUTHOR REVIEW": "AUR",
    "Formatting": "FORM",
    "Published": "PUB",
    "Rejected": "REJ",
    "Withdrawn": "WIT",
}

VALID_STATES = [
    AUTHOR_REV,
    AUTHOR_REVISIONS,
    COPY_EDIT,
    EDITOR_REVIEW,
    FORMATTING,
    IN_REF_REV,
    PUBLISHED,
    REJECTED,
    SUBMITTED,
    WITHDRAWN,
]

SAMPLE_MANU = {
    flds.TITLE: 'Short module import names in Python',
    flds.AUTHOR: 'Eugene Callahan',
    flds.REFEREES: [],
}


def get_states() -> list:
    return VALID_STATES


def is_valid_state(state: str) -> bool:
    return state in VALID_STATES


# actions:
ACCEPT = 'ACC'
ACCWITHREV = 'ACCWITHREV'
ASSIGN_REF = 'ARF'
DELETE_REF = 'DRF'
DONE = 'DON'
REJECT = 'REJ'
WITHDRAW = 'WIT'
# for testing:
TEST_ACTION = ACCEPT

VALID_ACTIONS = [
    ACCEPT,
    ACCWITHREV,
    ASSIGN_REF,
    DELETE_REF,
    DONE,
    REJECT,
    WITHDRAW,
]


def get_actions() -> list:
    return VALID_ACTIONS


def is_valid_action(action: str) -> bool:
    return action in VALID_ACTIONS


def assign_ref(manu: dict, ref: str, extra=None) -> str:
    print(extra)
    manu[flds.REFEREES].append(ref)
    return IN_REF_REV


def delete_ref(manu: dict, ref: str) -> str:
    if len(manu[flds.REFEREES]) > 0:
        manu[flds.REFEREES].remove(ref)
    if len(manu[flds.REFEREES]) > 0:
        return IN_REF_REV
    else:
        return SUBMITTED


FUNC = 'f'

COMMON_ACTIONS = {
    WITHDRAW: {
        FUNC: lambda **kwargs: WITHDRAWN,
    },
}

STATE_TABLE = {
    SUBMITTED: {
        ASSIGN_REF: {
            FUNC: assign_ref,
        },
        REJECT: {
            FUNC: lambda **kwargs: REJECTED,
        },
        **COMMON_ACTIONS,
    },
    IN_REF_REV: {
        ASSIGN_REF: {
            FUNC: assign_ref,
        },
        DELETE_REF: {
            FUNC: delete_ref,
        },
        ACCWITHREV: {
            FUNC: lambda **kwargs: AUTHOR_REVISIONS,
        },
        **COMMON_ACTIONS,
    },
    AUTHOR_REVISIONS: {
        DONE: {
            FUNC: lambda **kwargs: EDITOR_REVIEW,
        },
        **COMMON_ACTIONS,
    },
    EDITOR_REVIEW: {
        ACCEPT: {
            FUNC: lambda **kwargs: COPY_EDIT,
        },
        **COMMON_ACTIONS,
    },
    COPY_EDIT: {
        DONE: {
            FUNC: lambda **kwargs: AUTHOR_REV,
        },
        **COMMON_ACTIONS,
    },
    AUTHOR_REV: {
        DONE: {
            FUNC: lambda **kwargs: FORMATTING,
        },
        **COMMON_ACTIONS,
    },
    FORMATTING: {
        DONE: {
            FUNC: lambda **kwargs: PUBLISHED,
        },
        **COMMON_ACTIONS,
    },
    REJECTED: {
        **COMMON_ACTIONS,
    },
    WITHDRAWN: {
        **COMMON_ACTIONS,
    },
    PUBLISHED: {},
}


def get_valid_actions_by_state(state: str):
    valid_actions = STATE_TABLE[state].keys()
    print(f'{valid_actions=}')
    return valid_actions


def handle_action(curr_state, action, **kwargs) -> str:
    # Convert to FSM-recognized code if it's a long-form string
    curr_state = STATE_NAME_TO_CODE.get(curr_state, curr_state)

    if curr_state not in STATE_TABLE:
        raise ValueError(f'Bad state: {curr_state}')
    if action not in STATE_TABLE[curr_state]:
        raise ValueError(f'Invalid action {action} for state {curr_state}')
    return STATE_TABLE[curr_state][action][FUNC](**kwargs)


def main():
    print(handle_action(SUBMITTED, ASSIGN_REF,
                        manu=SAMPLE_MANU, ref='Jack'))
    print(handle_action(IN_REF_REV, ASSIGN_REF, manu=SAMPLE_MANU,
                        ref='Jill', extra='Extra!'))
    print(handle_action(IN_REF_REV, DELETE_REF, manu=SAMPLE_MANU,
                        ref='Jill'))
    print(handle_action(IN_REF_REV, DELETE_REF, manu=SAMPLE_MANU,
                        ref='Jack'))
    print(handle_action(SUBMITTED, WITHDRAW, manu=SAMPLE_MANU))
    print(handle_action(SUBMITTED, REJECT, manu=SAMPLE_MANU))


if __name__ == '__main__':
    main()
