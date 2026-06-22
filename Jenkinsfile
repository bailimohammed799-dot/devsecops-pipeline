pipeline {
    agent any

    environment {
        TARGET_REPO = 'gothinkster/flask-realworld-example-app'
        TARGET_COMMIT = '4b95fb2227dfeb5dd1a45d89b2bf48630b93fd28'
        MIN_COVERAGE = '60'
    }

    stages {
        stage('Stage 1: Source Retrieval') {
            steps {
                sh '''
                    git clone "https://github.com/${TARGET_REPO}.git" /tmp/conduit-app
                    cd /tmp/conduit-app
                    git checkout ${TARGET_COMMIT}
                    SHA=$(git rev-parse HEAD)
                    if [ "$SHA" != "${TARGET_COMMIT}" ]; then
                        echo "SHA mismatch!"
                        exit 1
                    fi
                    echo "Commit verified: $SHA"
                '''
            }
        }

        stage('Stage 2: Build') {
            steps {
                dir('/tmp/conduit-app') {
                    sh '''
                        pip install -r requirements.txt
                        python -c "import conduit; print('Build OK')"
                    '''
                }
            }
        }

        stage('Stage 3: SonarQube') {
            steps {
                sh '''
                    docker compose -f docker/docker-compose.yml up -d sonarqube
                    for i in $(seq 1 30); do
                        curl -s http://localhost:9000/api/system/status | grep -q '"UP"' && break
                        sleep 10
                    done
                    sonar-scanner \
                        -Dsonar.host.url=http://localhost:9000 \
                        -Dsonar.login=${SONAR_TOKEN} \
                        -Dsonar.projectKey=conduit \
                        -Dsonar.sources=/tmp/conduit-app/conduit \
                        -Dsonar.tests=/tmp/conduit-app/tests
                '''
            }
        }

        stage('Stage 4: Unit Tests') {
            steps {
                dir('/tmp/conduit-app') {
                    sh '''
                        pip install pytest pytest-cov
                        python -m pytest tests/ -v --junitxml=junit.xml \
                            --cov=conduit --cov-report=xml:coverage.xml
                    '''
                }
            }
        }

        stage('Stage 5: SAST') {
            steps {
                dir('/tmp/conduit-app') {
                    sh '''
                        pip install semgrep bandit pip-audit
                        semgrep scan --config p/owasp-top-ten --config p/python --sarif conduit/ || true
                        bandit -r conduit/ -f json -o bandit.json || true
                        pip-audit -r requirements.txt --format json --output pip-audit.json || true
                    '''
                }
            }
        }

        stage('Stage 6: Image Build') {
            steps {
                sh '''
                    docker build -t localhost:5000/conduit:latest \
                        -f docker/Dockerfile /tmp/conduit-app
                    docker run -d -p 5000:5000 --name registry registry:2 || true
                    docker push localhost:5000/conduit:latest
                    trivy image --severity HIGH,CRITICAL localhost:5000/conduit:latest || true
                '''
            }
        }

        stage('Stage 7: Deploy') {
            steps {
                sh '''
                    docker compose -f docker/docker-compose.yml up -d
                    for i in $(seq 1 30); do
                        curl -s -o /dev/null http://localhost:8080/api/ && break
                        sleep 5
                    done
                '''
            }
        }

        stage('Stage 8: DAST') {
            steps {
                sh '''
                    # ZAP baseline
                    docker run --rm --network host owasp/zap2docker-stable zap-baseline.py \
                        -t http://localhost:8080 || true
                    # Custom scenarios
                    pip install requests
                    for script in tests/security/scenario_*.py; do
                        python3 "$script" --url http://localhost:8080 || true
                    done
                '''
            }
        }

        stage('Stage 9: Reports') {
            steps {
                sh '''
                    python3 scripts/aggregate_reports.py reports/$(date +%Y%m%d-%H%M%S) jenkins-${BUILD_NUMBER}
                '''
            }
        }
    }

    post {
        always {
            sh 'docker compose -f docker/docker-compose.yml down -v || true'
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
        }
    }
}
