
package mlops.data

import future.keywords.if

default allow_data_access = false

# Allow data access based on role
allow_data_access if {
    input.user.role == "data_scientist"
    input.data.classification == "internal"
}

allow_data_access if {
    input.user.role == "admin"
}

# Deny sensitive data access
deny_data_access[msg] if {
    input.data.classification == "sensitive"
    input.user.role != "admin"
    msg := "Insufficient permissions for sensitive data"
}
