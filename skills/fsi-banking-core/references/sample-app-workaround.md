# マルチリージョン マイクロサービス・アプリケーション デプロイ時のエラー対応

マルチリージョン マイクロサービス・アプリケーションをデプロイする際に発生しうるエラーとその対応をまとめる。

## ケース 1: ECR へのログイン失敗

```
[xx%] fail: docker login --username AWS --password-stdin https://xxx.dkr.ecr.ap-northeast-1.amazonaws.com exited with error code 1: Error saving credentials: error storing credentials - err: exit status 1, out: `Post "http://ipc/registry/credstore-updated": dial unix backend.sock: connect: no such file or directory
```

**[原因と対応]**

ECR へのログインに失敗していることが原因。下記 docker 設定ファイル（`~/.docker/config.json`）の `credsStore` 属性を削除する。

```json
{
  "credsStore": "desktop"
}
```

## ケース 2: Docker デーモン未起動

```
docker build --tag cdkasset-298fda3b14e3cd7c554dacd230e74fd37b86b3b565313f4eecc0829404b3dd8a --platform linux/amd64 . exited with error code 1: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

**[原因と対応]**

デプロイ環境上で docker デーモンが起動していないことが原因。docker デーモンを起動させる。
