/**
 * @fileoverview 타입 정의
 * @description 프로젝트에서 사용하는 타입 선언
 * @author kevin1113dev
 */

import { Model } from "sequelize";
import { AudioPlayer } from '@discordjs/voice';
import Action from "./action.js";

/**
 * Sequelize 모델 타입
 */
export type DATA = Model<any, any>;

/**
 * TTS 큐 아이템 타입
 */
export type TTSQueueItem = {
  /** TTS 텍스트 */
  text: string;
  /** 화자 표시명 */
  displayName: string;
  /** 음성 이름 */
  voiceName: string | null;
  /** 속도 */
  speed: number | null;
  /** 피치 */
  pitch: string | undefined;
  /** 예상 재생 시간 (ms) */
  estimatedDuration: number;
};

/**
 * 길드(서버) 데이터 타입
 *
 * @remarks
 * 각 Discord 서버별로 오디오 플레이어, 액션 인스턴스, 타임아웃을 관리
 */
export type GuildData = {
  /** Discord 서버(길드) ID */
  guildId: string;

  /** 오디오 플레이어 인스턴스 */
  audioPlayer: AudioPlayer | null;

  /** 액션 관리 인스턴스 */
  action: Action;

  /** 30분 후 자동 퇴장을 위한 타임아웃 */
  timeOut: NodeJS.Timeout | null;

  /** TTS 큐 */
  ttsQueue: TTSQueueItem[];

  /** 현재 TTS 재생 중 여부 */
  isPlayingTTS: boolean;
};