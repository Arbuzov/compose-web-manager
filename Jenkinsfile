DIST_NAME = 'bullseye'
pipeline {
  agent none
  options {
    buildDiscarder(logRotator(daysToKeepStr: '183', artifactDaysToKeepStr: '183'))
    disableConcurrentBuilds()
    skipStagesAfterUnstable()
    newContainerPerStage()
  }
  stages {
    stage('SonarQube Analysis') {
      agent {
          docker { image 'sonarsource/sonar-scanner-cli' }
      }
      steps {
        script {
          if (env.CHANGE_ID) {
            env.putAt('SONAR_PULLREQUEST_KEY', env.CHANGE_ID)
            env.putAt('SONAR_PULLREQUEST_BRANCH', env.CHANGE_BRANCH)
            env.putAt('SONAR_PULLREQUEST_BASE', env.GIT_BRANCH)
          }
        }
        withSonarQubeEnv('SonarQube Server') {
          sh "sonar-scanner"
        }
      }
    }
    stage ('Build project') {
      agent {
        dockerfile {
          filename 'Dockerfile'
        }
      }
      environment {
        IS_DEVELOPMENT = "${((CHANGE_ID)||(GIT_BRANCH!='master'))}"
        DEB_VERSION_SUFFIX="${DIST_NAME}${IS_DEVELOPMENT=='true'?'.dev':''}.${env.BUILD_NUMBER}"
      }
      steps {
        sh """#!/bin/bash
        sudo rm -fR deb_dist
        sudo rm -fR deb
        install -d -m 777 deb_dist
        install -d -m 777 deb
        """
        
        sh """#!/bin/bash
        python3 setup.py --command-packages=stdeb3.command sdist_dsc \
                          --debian-version=${DEB_VERSION_SUFFIX} \
                          --dist-dir=${WORKSPACE}/deb_dist
        cp -f ${WORKSPACE}/deploy/debian/* ${WORKSPACE}/deb_dist/compose-web-manager-*/debian/
        cd ${WORKSPACE}/deb_dist/compose-web-manager-*/
        dpkg-buildpackage -rfakeroot -uc -us
        cp ${WORKSPACE}/deb_dist/*.deb ${WORKSPACE}/deb/
        rm -fR ${WORKSPACE}/deb_dist
        """
        stash includes: 'deb/*.deb', name: "package"
        
      }
      post {
        failure {
          archiveArtifacts artifacts: '**/**', fingerprint: false, onlyIfSuccessful: false
          print "Delete all on failure"
          cleanWs()
          deleteDir()
        }
        success {
          archiveArtifacts artifacts: 'deb/*.deb', fingerprint: false, onlyIfSuccessful: true
          print "Delete all on success"
          cleanWs()
          deleteDir()
        }
      }
    }
    stage ('Push deb package to the repository') {
      when { branch 'master' }
      agent {
        label 'local-deb-repo'
      }
      options { skipDefaultCheckout() }
      steps {
        sh """#!/bin/bash
        rm -fR deb
        """
        unstash "package"
        dir ('deb') {
          script {
            sh "cd /data/debian/ && sudo reprepro remove ${DIST_NAME} python3-compose-web-manager"
            sh "sudo reprepro -C main -b /data/debian/ includedeb ${DIST_NAME} python3-compose-web-manager*.deb"
            sh "rm python3-compose-web-manager*.deb"
          }
        }
      }
      post {
        cleanup {
          cleanWs()
          deleteDir()
        }
      }
    }
  }
}