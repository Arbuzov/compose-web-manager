def DIST_REPO = [
  'stretch':'scpc', 
  'buster':'buster', 
  'bullseye':'bullseye',
  'bookworm':'bookworm-local'
]

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
    stage ('Record issues') {
      agent {
          docker { image 'sonarsource/sonar-scanner-cli' }
      }
      steps {
        unstash "report"
        recordIssues(
          aggregatingResults: true,
           tools: [
            pyLint(pattern: '*-pylint.log', reportEncoding: 'UTF-8')
          ]
        )
      }         
    }
  }
}