pipeline {
    agent { label 'docker' }

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        // Use the same LXC address and credentials in the frontend Jenkinsfile.
        DEPLOY_HOST = '10.30.0.6'
        DEPLOY_SSH_CREDENTIALS = 'sgcc-web-deploy'
        DEPLOY_KNOWN_HOSTS_CREDENTIALS = 'sgcc-web-known-hosts'
        PVE_API_CREDENTIALS = 'sgcc-web-proxmox-api'
        PVE_URL = 'https://console.sgcc-wiki.org'
        PVE_NODE = 'sgcc'
        // Reserve a free VMID and keep these settings identical in both repos.
        LXC_VMID = '120'
        PVE_TEMPLATE = 'local:vztmpl/ubuntu-26.04-standard_26.04-1_amd64.tar.zst'
        PVE_STORAGE = 'hdd-cached'
        PVE_BRIDGE = 'sgcapps'
        LXC_IPV4_CIDR = '10.30.0.6/24'
        LXC_GATEWAY = '10.30.0.1'
        LXC_DNS = '163.239.1.1'
        LXC_MTU = '1450'
        SERVICE = 'sgcc-webp'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    def revision = checkout scm
                    env.SOURCE_BRANCH = env.BRANCH_NAME ?: revision.GIT_BRANCH ?: ''
                    env.IMAGE_REF = sh(
                        script: '''
                            printf '%s:%s-%s' "$SERVICE" "$(git rev-parse --short=12 HEAD)" \
                                "$(printf '%s' "$BUILD_TAG" | sha256sum | cut -c1-12)"
                        ''',
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --pull --network=host --platform=linux/amd64 --tag "$IMAGE_REF" .'
            }
        }

        stage('Provision and deploy') {
            when {
                expression {
                    !env.CHANGE_ID && env.SOURCE_BRANCH in ['main', 'origin/main']
                }
            }
            steps {
                // The identical lock in both repositories serializes shared-LXC updates.
                lock(resource: 'sgcc-web-lxc') {
                    withCredentials([
                        string(credentialsId: env.PVE_API_CREDENTIALS, variable: 'PVE_API_TOKEN'),
                        sshUserPrivateKey(credentialsId: env.DEPLOY_SSH_CREDENTIALS,
                            keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')
                    ]) {
                        sh '''#!/usr/bin/env bash
set -euo pipefail
umask 077
public_key_file=$(mktemp)
trap 'rm -f "$public_key_file"' EXIT
ssh-keygen -y -P '' -f "$SSH_KEY" > "$public_key_file"
SSH_PUBLIC_KEY_FILE="$public_key_file" python3 deploy/provision.py
'''
                    }
                    withCredentials([
                        sshUserPrivateKey(credentialsId: env.DEPLOY_SSH_CREDENTIALS,
                            keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                        file(credentialsId: env.DEPLOY_KNOWN_HOSTS_CREDENTIALS,
                            variable: 'KNOWN_HOSTS')
                    ]) {
                        sh 'bash deploy/deploy.sh'
                    }
                }
            }
        }
    }

    post {
        always {
            // Only remove this build's unique tag, preserving the shared Docker cache.
            sh 'if [ -n "${IMAGE_REF:-}" ]; then docker image rm "$IMAGE_REF" >/dev/null 2>&1 || true; fi'
        }
    }
}
