
package mlops.deployment

default allow_deployment = false

# Allow deployment if all conditions are met
allow_deployment {
    input.model.accuracy >= 0.80
    input.model.tested == true
    input.security.scanned == true
    input.security.vulnerabilities == 0
}

# Deny deployment if accuracy is too low
deny_deployment[msg] {
    input.model.accuracy < 0.80
    msg := sprintf("Model accuracy %.2f%% is below threshold 80%%", [input.model.accuracy * 100])
}

# Deny deployment if not tested
deny_deployment[msg] {
    input.model.tested == false
    msg := "Model has not been tested"
}

# Deny deployment if security vulnerabilities found
deny_deployment[msg] {
    input.security.vulnerabilities > 0
    msg := sprintf("Security scan found %d vulnerabilities", [input.security.vulnerabilities])
}
