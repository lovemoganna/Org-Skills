import React from 'react';
import {AbsoluteFill,Audio,Composition,Sequence,interpolate,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import example from '../specs/example.json';
import {VideoSpec} from './schema.mjs';

type Spec=Omit<typeof example, 'bgm' | 'narrationEnabled'> & {bgm?: {src:string;volume:number;fadeInSeconds:number;fadeOutSeconds:number}; narrationEnabled?: boolean};
const ease=(f:number,start=0)=>interpolate(f,[start,start+24],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
const Panel:React.FC<{children:React.ReactNode,style?:React.CSSProperties}>=({children,style})=><div style={{border:'1px solid #ffffff26',borderRadius:22,background:'#ffffff06',padding:32,...style}}>{children}</div>;
function Scene({scene,index,spec}:{scene:Spec['scenes'][number],index:number,spec:Spec}){
 const f=useCurrentFrame(), a=spec.theme.accent, p=ease(f), end=scene.seconds*spec.fps;
 const enter={opacity:p,transform:`translateY(${(1-p)*25}px)`};
 return <AbsoluteFill style={{opacity:interpolate(f,[end-9,end-1],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),padding:'145px 130px 125px',...enter}}>
   <div style={{fontSize:25,letterSpacing:4,color:a,marginBottom:28}}>{scene.eyebrow}</div>
   <div style={{fontSize:['hook','takeaway'].includes(scene.type)?104:64,fontWeight:700,lineHeight:1.25,whiteSpace:'pre-line',letterSpacing:-2}}>{scene.title}</div>
   {scene.type==='hook'&&<div style={{display:'flex',gap:22,marginTop:55,alignItems:'center'}}><div style={{width:86,height:6,background:a}}/><div style={{fontSize:31,color:'#9cabb8'}}>认知笔记 / 30 秒</div></div>}
   {scene.type==='equation'&&<div style={{display:'flex',gap:22,marginTop:65}}>{scene.items?.map((v,i)=><Panel key={v} style={{flex:1,opacity:ease(f,10+i*9),borderTop:`3px solid ${a}`}}><div style={{color:a,fontSize:22}}>0{i+1}</div><div style={{fontSize:48,marginTop:20}}>{v}</div></Panel>)}</div>}
   {scene.type==='comparison'&&<div style={{display:'flex',gap:30,marginTop:45}}>{scene.items?.map((v,i)=><Panel key={v} style={{flex:1}}><div style={{fontSize:32,color:i?a:'#a8b5c0'}}>{v}</div><svg width="660" height="170" viewBox="0 0 660 170"><path d={i?'M 25 140 L 145 128 L 255 90 L 365 105 L 480 55 L 620 20':'M 25 130 Q 110 100 180 130 T 340 130 T 500 130 L 620 130'} fill="none" stroke={i?a:'#788895'} strokeWidth="7" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-ease(f,20)}/></svg><div style={{fontSize:20,color:'#9cabb8'}}>路径示意 · 非统计数据</div></Panel>)}</div>}
   {scene.type==='steps'&&<div style={{display:'flex',gap:28,marginTop:65}}>{scene.items?.map((v,i)=><Panel key={v} style={{flex:1,opacity:ease(f,10+i*15)}}><div style={{fontSize:66,color:a,fontWeight:300}}>0{i+1}</div><div style={{fontSize:36,marginTop:24}}>{v}</div></Panel>)}</div>}
   {scene.type==='takeaway'&&<div style={{width:120+ease(f,20)*380,height:5,background:a,marginTop:55}}/>}
   <div style={{position:'absolute',left:130,bottom:142,fontSize:31,color:'#c0cad2'}}>{scene.subtitle}</div>
   {spec.narrationEnabled !== false && <Audio src={staticFile(scene.audio)}/>}
 </AbsoluteFill>;
}
function Video({spec}:{spec:Spec}){
 const f=useCurrentFrame();let from=0;const total=spec.scenes.reduce((n,s)=>n+Math.round(s.seconds*spec.fps),0);
 return <AbsoluteFill style={{background:spec.theme.background,color:spec.theme.foreground,fontFamily:'"Microsoft YaHei", "Noto Sans CJK SC", sans-serif'}}>
 {spec.bgm && <Audio src={staticFile(spec.bgm.src)} loop volume={(frame)=>spec.bgm!.volume*Math.min(1,frame/Math.max(1,spec.bgm!.fadeInSeconds*spec.fps),Math.max(0,(total-1-frame)/Math.max(1,spec.bgm!.fadeOutSeconds*spec.fps)))} loopVolumeCurveBehavior="extend"/>}
 <AbsoluteFill style={{transform:`scale(${spec.width/1920},${spec.height/1080})`,transformOrigin:'top left',width:1920,height:1080,background:'radial-gradient(ellipse at 90% 0%, #284350 0%, transparent 65%)'}}>
 <div style={{position:'absolute',top:50,left:130,right:130,display:'flex',justifyContent:'space-between',fontSize:22,color:'#9cabb8',letterSpacing:3}}><span>认知笔记 / KNOWLEDGE NOTES</span></div>
 {spec.scenes.map((s,i)=>{const start=from;from+=Math.round(s.seconds*spec.fps);return <Sequence key={i} from={start} durationInFrames={Math.round(s.seconds*spec.fps)}><Scene scene={s} index={i} spec={spec}/></Sequence>;})}
 <div style={{position:'absolute',left:130,right:130,bottom:60,display:'flex',justifyContent:'space-between',color:'#9cabb8',fontSize:22}}><span>{spec.title}</span><span>{String(Math.min(spec.scenes.length,1+spec.scenes.filter((_,i)=>f>=spec.scenes.slice(0,i+1).reduce((n,s)=>n+s.seconds*spec.fps,0)).length)).padStart(2,'0')} / {String(spec.scenes.length).padStart(2,'0')}</span></div>
 <div style={{position:'absolute',bottom:0,height:5,width:`${(f+1)/total*100}%`,background:spec.theme.accent}}/>
 </AbsoluteFill></AbsoluteFill>;
}
registerRoot(()=> <Composition id="KnowledgeVideo" component={Video} defaultProps={{spec:example}} width={1920} height={1080} fps={30} durationInFrames={900} calculateMetadata={({props})=>{const s=VideoSpec.parse(props.spec);return {width:s.width,height:s.height,fps:s.fps,durationInFrames:s.scenes.reduce((n,x)=>n+Math.round(x.seconds*s.fps),0)};}}/>);
