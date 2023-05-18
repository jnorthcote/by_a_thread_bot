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
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    imagePullPolicy: Always
    command:
    - sleep
    args:
    - 99d
'''
        }
    }
    stages {
        stage('Example') {
            options {
                // Timeout counter starts BEFORE agent is allocated
                //timeout(time: 1, unit: 'SECONDS')
            }
            steps {
                echo 'Hello World'
            }
        }
    }
}
