ROLES_PERMISSIONS = {
    'authenticated': ['activities', 'reports',
                      'reports-aid_disbursements',
                      'reports-results',
                      'reports-counterpart-funding',
                      'export', 'help', 'about'],
    'public': ['activities', 'reports',
               'reports-aid_disbursements',
               'reports-results',
               'reports-counterpart-funding',
               'export', 'help', 'about'],
    'desk-officer': ['sector-dashboard'],
    'management': ['sector-dashboard',
                   'reports-milestones',
                   'reports-psip_disbursements'],
    'admin': ['sector-dashboard'],
    'results-data-entry': ['sector-dashboard', 'results'],
    'results-data-design': ['sector-dashboard', 'results'],
    'piu-desk-officer': ['sector-dashboard', 'reports-project-bank'],
    'world-bank': ['world-bank']
}


VIEW_EDIT_PERMISSIONS = {
    'view': {
        'domestic': [],
        'external': [
            'reports-aid_disbursements',
            'reports-results']
    },
    'edit': {
        'domestic': [
            'reports-milestones',
            'reports-psip_disbursements',
            'reports-project-bank'
        ],
        'external': []
    }
}


def make_permissions_list(user):
    permissions = []
    for role in user.roles_list:
        permissions += ROLES_PERMISSIONS.get(role)
        if user.administrator:
            permissions += ROLES_PERMISSIONS.get('admin')
        if user.is_authenticated:
            permissions += ROLES_PERMISSIONS.get('authenticated')
        if user.permissions_dict['view'] == 'both':
            permissions += VIEW_EDIT_PERMISSIONS['view']['domestic']
            permissions += VIEW_EDIT_PERMISSIONS['view']['external']
        elif user.permissions_dict['view'] != 'none':
            permissions += VIEW_EDIT_PERMISSIONS['view'].get(
                user.permissions_dict['view'])

        if user.permissions_dict['edit'] == 'both':
            permissions += VIEW_EDIT_PERMISSIONS['edit']['domestic']
            permissions += VIEW_EDIT_PERMISSIONS['edit']['external']
        elif user.permissions_dict['edit'] != 'none':
            permissions += VIEW_EDIT_PERMISSIONS['edit'].get(
                user.permissions_dict['edit'])

    return list(set(permissions))
