pipeline {
    agent any
    environment {
        githubrepo = "https://github.com/prem6016/petclinic-flask.git"
        DOCKER_IMAGE = "prem6016/pet-clinic-flask:latest"
        REMOTE_USER = "ubuntu"
        REMOTE_HOST = "3.92.1.72"
        REMOTE_APP_DIR = "/home/ubuntu/petclinic"
        CONTAINER_NAME = "petclinic"
        HOST_PORT = "80"
        CONTAINER_PORT = "5000"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: "${githubrepo}"
            }
        }

        stage('Prepare Remote') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "
                    set -e
                    which docker || (sudo apt update && sudo apt install -y docker.io && sudo systemctl start docker)
                    mkdir -p ${REMOTE_APP_DIR}
                    "
                    """
                }
            }
        }

        stage('Sync Code') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                    rsync -avz --delete \
                        --exclude '__pycache__/' \
                        --exclude '*.pyc' \
                        --exclude '.git/' \
                        --exclude '.vscode/' \
                        ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_APP_DIR}/
                    """
                }
            }
        }

        stage('Build & Push Image') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_HUB_USERNAME', passwordVariable: 'DOCKER_HUB_PASSWORD')
                ]) {
                    sshagent(['ec2-ssh-key']) {
                        sh """
                        ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "
                        set -e
                        cd ${REMOTE_APP_DIR}
                        docker build -t ${DOCKER_IMAGE} .
                        echo \"${DOCKER_HUB_PASSWORD}\" | docker login -u \"${DOCKER_HUB_USERNAME}\" --password-stdin
                        docker push ${DOCKER_IMAGE}
                        docker logout
                        "
                        """
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "
                    set -e
                    docker pull ${DOCKER_IMAGE}
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                    docker run -d --name ${CONTAINER_NAME} -p ${HOST_PORT}:${CONTAINER_PORT} ${DOCKER_IMAGE}
                    "
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Deployment completed'
        }
    }
}
