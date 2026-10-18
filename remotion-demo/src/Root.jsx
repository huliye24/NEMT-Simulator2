import React from 'react';
import {Composition} from 'remotion';
import {NEMTDemo} from './NEMTDemo.jsx';

export const RemotionRoot = () => {
  return (
    <Composition
      id="NEMTDemo"
      component={NEMTDemo}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
