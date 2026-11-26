"""Generate natural-rate Edge neural speech; never speed up or truncate speech."""
import argparse, asyncio, json, subprocess
from pathlib import Path
import edge_tts

parser=argparse.ArgumentParser()
parser.add_argument('--spec',default='specs/example.json')
parser.add_argument('--voice',default='zh-CN-YunxiNeural')
parser.add_argument('--rate',default='+10%')
args=parser.parse_args()

async def main():
    spec=json.loads(Path(args.spec).read_text(encoding='utf-8'))
    report={'voice':args.voice,'rate':args.rate,'postSpeedup':False,'scenes':[]}
    for scene in spec['scenes']:
        target=Path('public')/scene['audio']
        target.parent.mkdir(parents=True,exist_ok=True)
        raw=target.with_suffix('.mp3')
        await asyncio.wait_for(edge_tts.Communicate(scene['narration'],args.voice,rate=args.rate).save(str(raw)),timeout=60)
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(raw)],encoding='utf-8'))
        if duration>scene['seconds']-0.4:
            raise ValueError(f'Speech {duration}s exceeds scene {scene["seconds"]}s; shorten text or extend scene.')
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(raw),'-af','adelay=80:all=1,apad','-t',str(scene['seconds']),'-ar','48000','-ac','1',str(target)],check=True)
        row={'audio':scene['audio'],'speechSeconds':duration,'sceneSeconds':scene['seconds'],'text':scene['narration']}
        report['scenes'].append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
    Path('renders').mkdir(exist_ok=True)
    Path('renders/edge-voice-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

asyncio.run(main())
