''' The original audio visualization '''
import numpy
from PIL import Image, ImageDraw


def init():
    global mem
    mem = {
        'smoothConstantDown' : 0.08,
        'smoothConstantUp' : 0.8,
        'lastSpectrum' : None,
    }

def frameRender(frameNo, frame, backgroundImage, completeAudioArray, sampleSize):
    global mem
    print(frameNo)
    mem['lastSpectrum'] = transformData(frameNo, completeAudioArray, sampleSize,\
                mem['smoothConstantDown'], mem['smoothConstantUp'], mem['lastSpectrum'])
    frame = drawBars(mem['lastSpectrum'], backgroundImage, (255,255,255))
    return frame

def transformData(i, completeAudioArray, sampleSize, smoothConstantDown, smoothConstantUp, lastSpectrum):
    if len(completeAudioArray) < (i + sampleSize):
      sampleSize = len(completeAudioArray) - i
    numpy.seterr(divide='ignore')
    window = numpy.hanning(sampleSize)
    data = completeAudioArray[i:i+sampleSize][::1] * window
    paddedSampleSize = 2048
    paddedData = numpy.pad(data, (0, paddedSampleSize - sampleSize), 'constant')
    spectrum = numpy.fft.fft(paddedData)
    sample_rate = 44100
    frequencies = numpy.fft.fftfreq(len(spectrum), 1./sample_rate)

    y = abs(spectrum[0:int(paddedSampleSize/2) - 1])

    # filter the noise away
    # y[y<80] = 0

    y = 20 * numpy.log10(y)
    y[numpy.isinf(y)] = 0

    if lastSpectrum is not None:
      lastSpectrum[y < lastSpectrum] = y[y < lastSpectrum] * smoothConstantDown + lastSpectrum[y < lastSpectrum] * (1 - smoothConstantDown)
      lastSpectrum[y >= lastSpectrum] = y[y >= lastSpectrum] * smoothConstantUp + lastSpectrum[y >= lastSpectrum] * (1 - smoothConstantUp)
    else:
      lastSpectrum = y

    x = frequencies[0:int(paddedSampleSize/2) - 1]

    return lastSpectrum
    
def drawBars(spectrum, image, color):
    imTop = Image.new("RGBA", (1280, 360))
    draw = ImageDraw.Draw(imTop)
    r, g, b = color
    color2 = (r, g, b, 50)
    for j in range(0, 63):
      draw.rectangle((10 + j * 20, 325, 10 + j * 20 + 20, 325 - spectrum[j * 4] * 1 - 10), fill=color2)
      draw.rectangle((15 + j * 20, 320, 15 + j * 20 + 10, 320 - spectrum[j * 4] * 1), fill=color)


    imBottom = imTop.transpose(Image.FLIP_TOP_BOTTOM)

    im = Image.new("RGB", (1280, 720), "black")
    im.paste(image, (0, 0))
    im.paste(imTop, (0, 0), mask=imTop)
    im.paste(imBottom, (0, 360), mask=imBottom)

    return im
