pipeline {
    //agent none
    //agent { label 'jenkins=slave' }
    agent {
        kubernetes {
            defaultContainer 'kaniko'
            yaml '''
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24.0.0-cli-alpine3.18
    imagePullPolicy: Always
'''
        }
    }
    stages {
        stage('Example') {
            options {
                // Timeout counter starts BEFORE agent is allocated
                timeout(time: 300, unit: 'SECONDS')
            }
            steps {
                echo 'Hello World'
                sh '''
                    docker -v
                '''
            }
        }
    }
}
