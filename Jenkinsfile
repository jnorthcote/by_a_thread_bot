pipeline {
    //agent none
    //agent { label 'jenkins=slave' }
    agent {
        kubernetes {
            defaultContainer 'docker'
            yaml '''
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24.0.0-cli-alpine3.18
    imagePullPolicy: Always
    command:
    - sleep
    args:
    - 99d
'''
        }
    }
    stages {
        stage('Build') {
            options {
                // Timeout counter starts BEFORE agent is allocated
                timeout(time: 300, unit: 'SECONDS')
            }
            steps {
                sh '''
                    docker compose -f dc-bot.yml build
                '''
            }
        }
    }
}
