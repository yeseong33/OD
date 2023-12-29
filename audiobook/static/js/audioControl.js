function playAudio(element) {
    var audio = element.querySelector('.voice-sample');
    audio.play();
  }

  function stopAudio(element) {
    var audio = element.querySelector('.voice-sample');
    audio.pause();
    audio.currentTime = 0; // 오디오 재생 위치를 처음으로 리셋합니다.
  }