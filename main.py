<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terabox Video Fetcher</title>
    <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
    <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
    <style>
        .video-js {
            margin: 0 auto;
            display: block;
            width: 100%;
            height: 100vh;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
    </style>
    <script>
        function extractVideoId(url) {
            const parts = url.split('/');
            return parts[parts.length - 1];
        }

        function loadVideo(videoUrl) {
            const videoContainer = document.getElementById('video-container');
            videoContainer.innerHTML = `
                <video id="video-player" class="video-js" controls preload="auto" width="100%" height="100%">
                    <source src="${videoUrl}" type="application/x-mpegURL">
                </video>
            `;
            const videoPlayer = videojs(document.getElementById('video-player'));
            videoPlayer.on('error', function() {
                console.error('Error loading video:', videoPlayer.error());
                console.log('Video URL:', videoUrl);
                alert('Error loading video. Please try again.');
            });
        }

        function loadVideoFromUrl() {
            const params = new URLSearchParams(window.location.search);
            const url = params.get('url');
            if (url) {
                const videoId = extractVideoId(url);
                const videoUrl = `https://jolly-union-9cc3.shraj.workers.dev/?id=${videoId}`;
                console.log('Video URL:', videoUrl);
                loadVideo(videoUrl);
            }
        }

        window.onload = loadVideoFromUrl;
    </script>
</head>

<body>
    <div id="video-container"></div>
</body>

</html>
