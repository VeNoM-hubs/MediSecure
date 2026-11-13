pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    IMAGE_NAME = 'medisecure-web'
    IMAGE_TAG  = 'latest'
    FULL_IMAGE = "${IMAGE_NAME}:${IMAGE_TAG}"
    K8S_DIR    = 'k8s'
    NAMESPACE  = 'medisecure'
    DEPLOYMENT = 'medisecure-web'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'ls -la'
      }
    }

    stage('Build Docker Image') {
      steps {
        sh '''
          set -eu
          docker build -t "${FULL_IMAGE}" .
          docker images "${IMAGE_NAME}"
        '''
      }
    }

    stage('Trivy Security Scan') {
      steps {
        sh '''
          set -eu
          if command -v trivy >/dev/null 2>&1; then
            trivy image --severity CRITICAL --exit-code 0 --no-progress "${FULL_IMAGE}"
          else
            echo "Trivy not installed on this agent — skipping image scan (demo)."
          fi
        '''
      }
    }

    stage('Deploy to K3s') {
      steps {
        sh '''
          set -eu

          # Import the locally built image into K3s containerd (no external registry).
          docker save "${FULL_IMAGE}" | sudo k3s ctr images import -

          # Apply Kubernetes manifests
          sudo k3s kubectl apply -f "${K8S_DIR}/deployment.yaml"
          sudo k3s kubectl apply -f "${K8S_DIR}/service.yaml"

          # Restart pods so they pick up a freshly imported :latest image
          sudo k3s kubectl -n "${NAMESPACE}" rollout restart deployment/"${DEPLOYMENT}"
        '''
      }
    }

    stage('Verify Deployment') {
      steps {
        sh '''
          set -eu
          sudo k3s kubectl -n "${NAMESPACE}" rollout status deployment/"${DEPLOYMENT}" --timeout=180s
          sudo k3s kubectl -n "${NAMESPACE}" get pods,svc -l app="${DEPLOYMENT}" -o wide
          echo "NodePort access (on the EC2 host): http://<EC2_PUBLIC_IP>:30081"
        '''
      }
    }
  }

  post {
    success {
      echo "MediSecure static portal deployed successfully."
    }
    failure {
      echo "Pipeline failed — check Docker build, Trivy, or kubectl output above."
    }
  }
}
