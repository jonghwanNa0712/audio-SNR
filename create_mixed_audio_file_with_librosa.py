# -*- coding: utf-8 -*-
import argparse
import array
import librosa
import math
import numpy as np
import random
import soundfile as sf


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean_file', type=str, required=True)
    parser.add_argument('--noise_file', type=str, required=True)
    parser.add_argument('--output_mixed_file', type=str, default='', required=True)
    parser.add_argument('--output_clean_file', type=str, default='')
    parser.add_argument('--output_noise_file', type=str, default='')
    parser.add_argument('--snr', type=float, default='', required=True)
    args = parser.parse_args()
    return args

def cal_adjusted_rms(clean_rms, snr):
    a = float(snr) / 20
    noise_rms = clean_rms / (10**a) 
    return noise_rms

def cal_amp(wf, dtype):
    buffer = wf.readframes(wf.getnframes())
    # The dtype depends on the value of pulse-code modulation. The int16 is set for 16-bit PCM.
    amptitude = (np.frombuffer(buffer, dtype=dtype)).astype(np.float64)
    return amptitude

def cal_rms(amp):
    return np.sqrt(np.mean(np.square(amp), axis=-1))

def save_waveform(output_path, amp, samplerate):
    # output_file = wave.Wave_write(output_path)
    # output_file.setparams(params) #nchannels, sampwidth, framerate, nframes, comptype, compname
    # output_file.writeframes(array.array('h', amp.astype(np.float64)).tobytes() )
    # output_file.close()
    sf.write(output_path, amp, samplerate)

if __name__ == '__main__':
    args = get_args()

    clean_file = args.clean_file
    noise_file = args.noise_file

    metadata = sf.info(clean_file)
    clean_amp, clean_samplerate = sf.read(clean_file, dtype='float64')
    noise_amp, noise_samplerate = sf.read(noise_file, dtype='float64')

    print(metadata.subtype_info)
    print(metadata)
    if metadata.subtype_info == '64 bit float':
        print("64bits")    

    # clean_amp = cal_amp(clean_wav, 'float64')
    # noise_amp = cal_amp(noise_wav, 'float64')

    clean_rms = cal_rms(clean_amp)
    print('clean_rms', clean_rms)

    start = random.randint(0, len(noise_amp)-len(clean_amp))
    divided_noise_amp = noise_amp[start: start + len(clean_amp)]
    noise_rms = cal_rms(divided_noise_amp)

    snr = args.snr
    adjusted_noise_rms = cal_adjusted_rms(clean_rms, snr)
    
    adjusted_noise_amp = divided_noise_amp * (adjusted_noise_rms / noise_rms) 
    mixed_amp = (clean_amp + adjusted_noise_amp)

    #Avoid clipping noise
    max_limit = np.finfo(clean_amp.dtype).max
    min_limit = np.finfo(clean_amp.dtype).min
    if mixed_amp.max(axis=0) > max_limit or mixed_amp.min(axis=0) < min_limit:
        if mixed_amp.max(axis=0) >= abs(mixed_amp.min(axis=0)): 
            reduction_rate = max_limit / mixed_amp.max(axis=0)
        else :
            reduction_rate = min_limit / mixed_amp.min(axis=0)
        mixed_amp = mixed_amp * (reduction_rate)
        clean_amp = clean_amp * (reduction_rate)

    save_waveform(args.output_mixed_file, mixed_amp, clean_samplerate)

