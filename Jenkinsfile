pipeline {
    agent any


    parameters {
        // Leave empty for a normal build. Enter an old tag to roll back to it.
        string(name: 'DEPLOY_TAG', defaultValue: '', description: 'Rollback only: tag to deploy, e.g. 2026.11.20-3')
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Downloading the latest team code from GitHub...'
                checkout scm
                sh 'git log -1 --pretty="Latest commit: %h by %an - %s"'
            }
        }

        stage('Rollback: Get Old Version') {
            when { expression { params.DEPLOY_TAG?.trim() } }
            steps {
                sh '''
                    echo "Rolling back to tag $DEPLOY_TAG"
                    git fetch --tags
                    git checkout "$DEPLOY_TAG" -- index.html
                    echo "$DEPLOY_TAG" > tag.txt
                '''
            }
        }

        stage('Validate Page') {
            steps {
                echo 'Checking that every section is present and all tags are closed...'
                sh 'python3 check_page.py'
            }
        }

        stage('Create Tag') {
            when { expression { !params.DEPLOY_TAG?.trim() } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token',
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    sh '''
                        AUTHOR=$(git log -1 --pretty=%an | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')
                        TAG="$(date +%Y.%m.%d)-$BUILD_NUMBER-$AUTHOR"
                        git config user.name "Jenkins"
                        git config user.email "jenkins@localhost"
                        git tag -a "$TAG" -m "Passed build $BUILD_NUMBER"
                        REPO=$(git config remote.origin.url | sed 's#https://##')
                        git push "https://$GIT_USER:$GIT_TOKEN@$REPO" "$TAG"
                        echo "$TAG" > tag.txt
                        echo "Created and pushed tag $TAG"
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    TAG=$(cat tag.txt)
                    mkdir -p /data/site
                    sed "s/{{VERSION}}/$TAG/" index.html > /data/site/index.html
                    echo "Deployed version $TAG - open http://localhost:8081"
                '''
            }
        }
    }

    post {
        success { echo 'PIPELINE PASSED: page tagged and deployed' }
        failure { echo 'PIPELINE FAILED: no tag created, live site unchanged' }
    }
}
