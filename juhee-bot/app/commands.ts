/**
 * @fileoverview Discord 슬래시 커맨드 정의
 * @description 봇이 사용하는 모든 슬래시 커맨드를 정의
 * @author kevin1113dev
 */

import { ChannelType, SlashCommandBuilder, SlashCommandOptionsOnlyBuilder } from 'discord.js';

const Commands: SlashCommandBuilder | Omit<SlashCommandBuilder, "addSubcommand" | "addSubcommandGroup"> | SlashCommandOptionsOnlyBuilder[] = [
  new SlashCommandBuilder()
    .setName('들어와')
    .setDescription('음성채널에 참가합니다.'),

  new SlashCommandBuilder()
    .setName('나가')
    .setDescription('음성채널에서 나갑니다.'),

  new SlashCommandBuilder()
    .setName('채널설정')
    .setDescription('tts 채널을 설정합니다.')
    .addChannelOption(option =>
      option.setName('채널')
        .setDescription('tts를 재생할 채널')
        .addChannelTypes(ChannelType.GuildText, ChannelType.GuildVoice)
        .setRequired(true)),

  new SlashCommandBuilder()
    .setName('채널해제')
    .setDescription('tts 채널을 해제합니다.'),

  new SlashCommandBuilder()
    .setName('목소리')
    .setDescription('목소리를 변경합니다.')
    .addStringOption(option =>
      option.setName('목소리')
        .setDescription('목소리')
        .addChoices(
          { name: '여성 A (차분)', value: 'female_a' },
          { name: '여성 B (밝음)', value: 'female_b' },
          { name: '여성 C (뉴스)', value: 'female_c' },
          { name: '남성 A (차분)', value: 'male_a' },
          { name: '남성 B (친근)', value: 'male_b' },
          { name: '남성 C (중후)', value: 'male_c' },
          { name: '🧒 아이', value: 'child' },
          { name: '👵 할머니', value: 'grandma' },
          { name: '🎸 락커', value: 'rocker' },
          { name: '😎 조폭', value: 'gangster' },
          { name: '🤓 오타쿠', value: 'otaku' },
          { name: '🌸 애니 소녀', value: 'anime_girl' },
          { name: '⚔️ 애니 소년', value: 'anime_boy' },
          { name: '🛡️ 게임 영웅', value: 'game_hero' },
          { name: '🦹 게임 악당', value: 'game_villain' },
          { name: '📖 나레이터', value: 'narrator' },
          { name: '😤 사나운 아줌마', value: 'angry_auntie' },
          { name: '🌏 외노자', value: 'foreigner' },
          { name: '🤖 로봇', value: 'robot' },
          { name: '🎬 인간극장 (남)', value: 'human_theater_m' },
          { name: '🎬 인간극장 (여)', value: 'human_theater_f' },
          { name: '🐉 드라곤', value: 'starcraft_dragon' },
          { name: '📺 홈쇼핑', value: 'homeshopping' },
          { name: '💂 군대 교관', value: 'drill_sergeant' },
          { name: '🍺 취한 부장님', value: 'drunk_boss' },
        )
        .setRequired(true)),

  new SlashCommandBuilder()
    .setName('피치')
    .setDescription('음높이를 변경합니다.')
    .addStringOption(option =>
      option.setName('피치값')
        .setDescription('음높이')
        .addChoices(
          { name: '매우 낮음', value: 'x-low' },
          { name: '낮음', value: 'low' },
          { name: '보통', value: 'medium' },
          { name: '높음', value: 'high' },
          { name: '매우 높음', value: 'x-high' },
        )
        .setRequired(true)),

  new SlashCommandBuilder()
    .setName('속도')
    .setDescription('tts 속도를 변경합니다. (0: 느림, 100: 빠름)')
    .addIntegerOption(option =>
      option.setName('속도값')
        .setDescription('tts 속도')
        .setMinValue(0)
        .setMaxValue(100)
        .setRequired(true)),

  new SlashCommandBuilder()
    .setName('닉네임읽기')
    .setDescription('메시지 앞에 닉네임을 읽어줍니다.')
    .addBooleanOption(option =>
      option.setName('활성화')
        .setDescription('닉네임 읽기 활성화/비활성화')
        .setRequired(true))
    .addIntegerOption(option =>
      option.setName('앞글자')
        .setDescription('닉네임 앞에서 몇 글자 읽을지 (0=읽지않음, 기본값=전체)')
        .setMinValue(0)
        .setMaxValue(4)
        .setRequired(false))
    .addIntegerOption(option =>
      option.setName('뒷글자')
        .setDescription('닉네임 뒤에서 몇 글자 읽을지 (0=읽지않음, 기본값=전체)')
        .setMinValue(0)
        .setMaxValue(4)
        .setRequired(false)),

  new SlashCommandBuilder()
    .setName('현재설정')
    .setDescription('현재 설정 된 목소리, 피치, 속도, 닉네임읽기를 확인합니다.'),

  new SlashCommandBuilder()
    .setName('음소거')
    .setDescription('봇이 채팅을 치지 않도록 음소거합니다.'),

  new SlashCommandBuilder()
    .setName('음소거해제')
    .setDescription('봇의 음소거를 해제합니다.'),
];

export default Commands;
