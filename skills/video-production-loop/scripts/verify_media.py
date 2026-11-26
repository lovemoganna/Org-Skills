"""Verify actual video against VideoSpec and extract review frames. Requires FFmpeg."""
import argparse,array,hashlib,json,math,subprocess,sys
from fractions import Fraction
from pathlib import Path

def run(argv):
    return subprocess.run(argv,check=True,capture_output=True).stdout

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video',required=True,type=Path)
    p.add_argument('--spec',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--audio',choices=['required','optional','forbidden'],default='required')
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    report={'video':str(a.video.resolve()),'spec':str(a.spec.resolve()),'checks':{},'subjectiveReview':'not_checked'}
    try:
        s=json.loads(a.spec.read_text(encoding='utf-8-sig'))
        fps=s['fps'];durations=[x['seconds']*fps for x in s['scenes']]
        if not durations or any(n<=0 or abs(n-round(n))>1e-6 for n in durations):raise ValueError('Scene durations must be positive whole frames')
        frames=sum(round(n) for n in durations);seconds=frames/fps
        probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(a.video)]))
        v=next(x for x in probe['streams'] if x['codec_type']=='video')
        has_audio=any(x['codec_type']=='audio' for x in probe['streams'])
        c=report['checks'];c['nonempty']=a.video.stat().st_size>0
        c['dimensions']=(v['width'],v['height'])==(s['width'],s['height'])
        c['fps']=Fraction(v['avg_frame_rate'])==Fraction(str(fps))
        c['frames']=int(v['nb_read_frames'])==frames
        c['duration']=abs(float(probe['format']['duration'])-seconds)<=max(.05,1/fps)
        c['audioPresence']=has_audio if a.audio=='required' else not has_audio if a.audio=='forbidden' else True
        run(['ffmpeg','-v','error','-xerror','-i',str(a.video),'-f','null','-']);c['fullDecode']=True
        if has_audio:
            # Analyse decoded interleaved stereo sample peaks; this is not true-peak or listening review.
            raw=run(['ffmpeg','-v','error','-i',str(a.video),'-vn','-ac','2','-ar','16000','-f','f32le','-'])
            samples=array.array('f');samples.frombytes(raw)
            if sys.byteorder!='little':samples.byteswap()
            peak=max(map(abs,samples),default=0)
            rms=math.sqrt(sum(x*x for x in samples)/max(1,len(samples)))
            report['audio']={'samplePeak':peak,'rmsDbfs':20*math.log10(rms) if rms else None}
            c['audioFinite']=math.isfinite(peak) and math.isfinite(rms)
            c['audioBelowFullScale']=peak<1
            if a.audio=='required':c['audioNonSilent']=rms>1e-6
        indices={0,frames-1};start=0
        for count in durations:
            count=round(count);indices.update([start,start+count//2]);
            if start:indices.add(start-1)
            start+=count
        indices=sorted(indices)
        frame_dir=a.out/'frames';frame_dir.mkdir(exist_ok=True)
        expression='+'.join(f'eq(n\\,{n})' for n in indices)
        run(['ffmpeg','-y','-v','error','-i',str(a.video),'-vf','select='+expression,'-fps_mode','vfr',str(frame_dir/'review-%03d.png')])
        report['reviewFrames']=[{'frame':n,'seconds':n/fps,'file':str(frame_dir/f'review-{i:03}.png')} for i,n in enumerate(indices,1)]
        c['reviewFramesExtracted']=all(Path(x['file']).is_file() for x in report['reviewFrames'])
        with a.video.open('rb') as f:report['sha256']=hashlib.file_digest(f,'sha256').hexdigest()
        report['expected']={'frames':frames,'seconds':seconds,'width':s['width'],'height':s['height'],'fps':fps}
    except Exception as e:
        report['error']=str(e)
        if isinstance(e,subprocess.CalledProcessError):report['toolError']=e.stderr.decode('utf-8',errors='replace')[-3000:]
    report['passed']=bool(report['checks']) and all(report['checks'].values()) and 'error' not in report
    (a.out/'media-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'checks':report['checks'],'error':report.get('error')},ensure_ascii=False))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
