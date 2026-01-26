
set -e

echo "🚀 Building Voicera (Aria + Orion only)..."
echo "⏱️  Removing unnecessary dependencies (langchain-chroma)..."

DOCKER_BUILDKIT=1 docker build \
    -f Dockerfile.optimized \
    -t voicera:aria-orion \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

echo "✅ Build complete!"
echo "📊 Image size:"
docker images voicera:aria-orion

echo ""
echo "📝 Next steps:"
echo "  docker push your-registry/voicera:aria-orion"
echo "  OR"
echo "  docker run -p 8000:8000 voicera:aria-orion"
