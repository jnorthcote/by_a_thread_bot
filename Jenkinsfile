pipeline {
    //agent none
    //agent { label 'jenkins=slave' }
    agent {
        kubernetes {
            defaultContainer 'kaniko'
            yaml '''
kind: Pod
metadata:
  name: kaniko
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug-v0.19.0
    imagePullPolicy: Always
    command:
    - /busybox/cat
    tty: true
'''
        }
    }
    environment {
        PROJECT_ID="narmb-369710"
        IMAGE_PUSH_DESTINATION="us-west1-docker.pkg.dev/${PROJECT_ID}/bat-bot/bat-bot-app:${BUILD_TAG}"
    }
    stages {
        stage('Build with Kaniko') {
            steps {
                checkout scm
                container(name: 'kaniko', shell: '/busybox/sh') {
                    withCredentials([file(credentialsId: 'docker-credentials', variable: 'DOCKER_CONFIG_JSON')]) {
                        withEnv(['PATH+EXTRA=/busybox']) {
                            sh '''#!/busybox/sh
                                cp $DOCKER_CONFIG_JSON /kaniko/.docker/config.json
                                echo "$IMAGE_PUSH_DESTINATION"
                                /kaniko/executor --context "." --dockerfile "./src/Dockerfile" --destination "$IMAGE_PUSH_DESTINATION"
                            '''
                        }
                    }
                }
            }
        }
    }
}
