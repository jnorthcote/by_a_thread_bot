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
    volumeMounts:
    - mountPath: /kaniko-cache
      name: kaniko-cache
  - name: cloud-sdk
    image: us-west1-docker.pkg.dev/narmb-369710/cicd-scars/cloud-sdk:alpine-kubectl
    imagePullPolicy: Always
    command:
      - sleep
      - "36000"
    tty: true
  volumes:
  - name: kaniko-cache
    persistentVolumeClaim:
      claimName: kaniko-cache-claim
'''
        }
    }
    environment {
        PROJECT_ID="narmb-369710"
        IMAGE_PUSH_DESTINATION="us-west1-docker.pkg.dev/${PROJECT_ID}/bat-bot/bat-bot-app:${BUILD_ID}"
    }
    stages {
        stage('Build with Kaniko') {
            steps {
                //checkout scm
                container(name: 'kaniko', shell: '/busybox/sh') {
                    withCredentials([file(credentialsId: 'docker-credentials', variable: 'DOCKER_CONFIG_JSON')]) {
                        withEnv(['PATH+EXTRA=/busybox']) {
                            sh '''#!/busybox/sh
                                cp $DOCKER_CONFIG_JSON /kaniko/.docker/config.json
                                echo "Image artifact destination: $IMAGE_PUSH_DESTINATION"
                                // /kaniko/executor --help
                                /kaniko/executor --cache=true --cache-dir=/kaniko-cache --context "." --dockerfile "./src/Dockerfile" --destination "$IMAGE_PUSH_DESTINATION"
                            '''
                        }
                    }
                }
            }
        }
        stage('Auth') {
            steps {
                container(name: 'cloud-sdk', shell: '/bin/sh') {
                    // withCredentials([file(credentialsId: 'bat-bot-token', variable: 'KUBE_TOKEN')]) {
                        // withEnv(['PATH+EXTRA=/busybox']) {
                            sh '''#!/bin/sh
                                gcloud container clusters get-credentials nova-ocr-bot-cluster --region us-west1
                            '''
                        // }
                    // }
                }
            }
        }
        stage('Deploy') {
            steps {
                container(name: 'cloud-sdk', shell: '/bin/sh') {
                    // withCredentials([file(credentialsId: 'bat-bot-token', variable: 'KUBE_TOKEN')]) {
                        // withEnv(['PATH+EXTRA=/busybox']) {
                            sh '''#!/bin/sh
                                echo 'Current Deployment Image'
                                kubectl -n bat-bot get deployment/by-a-thread-bot-deployment -o wide
                                kubectl -n bat-bot set image deployment/by-a-thread-bot-deployment by-a-thread-bot=$IMAGE_PUSH_DESTINATION
                                echo 'Updated Deployment Image'
                                kubectl -n bat-bot get deployment/by-a-thread-bot-deployment -o wide
                            '''
                        // }
                    // }
                }
            }
        }
        // stage('Deploy') {
        //     steps {
        //         container(name: 'k8s', shell: '/bin/sh') {
        //             withCredentials([file(credentialsId: 'bat-bot-token', variable: 'KUBE_TOKEN')]) {
        //                 withEnv(['PATH+EXTRA=/busybox']) {
        //                     sh '''#!/bin/sh
        //                         #kubectl -n bat-bot --token KUBE_TOKEN set image deployment/by-a-thread-bot-deployment by-a-thread-bot=$IMAGE_PUSH_DESTINATION
        //                         kubectl -n bat-bot get deployment/by-a-thread-bot-deployment -o json
        //                     '''
        //                 }
        //             }
        //         }
        //     }
        // }
    }
}
