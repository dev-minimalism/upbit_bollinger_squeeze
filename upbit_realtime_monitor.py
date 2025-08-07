# upbit_realtime_monitor.py
"""
업비트 실시간 변동성 폭파 볼린저 밴드 모니터링 시스템
- Heartbeat 기능 (1시간마다 상태 알림)
- 한국 시간 기준 24시간 거래
- 자동 재시작 및 오류 복구
- 텔레그램 알림 시스템
"""

import asyncio
import logging
import os
import re
import threading
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import pyupbit
import requests
from telegram.ext import Application, CommandHandler

warnings.filterwarnings('ignore')


class UpbitRealTimeVolatilityMonitor:
  def __init__(self, telegram_bot_token: str = None, telegram_chat_id: str = None):
    """
    업비트 실시간 변동성 폭파 볼린저 밴드 모니터링 시스템

    Parameters:
    telegram_bot_token: 텔레그램 봇 토큰
    telegram_chat_id: 텔레그램 채팅 ID
    """
    # 로깅 설정 (use logger configured in main.py)
    self.logger = logging.getLogger(__name__)

    # Ticker to Korean name mapping
    self.ticker_to_korean = {
      # 메이저 코인
      'KRW-BTC': '비트코인',
      'KRW-ETH': '이더리움',
      'KRW-XRP': '리플',
      'KRW-ADA': '에이다',
      'KRW-DOT': '폴카닷',
      # 대형 알트코인
      'KRW-LINK': '체인링크',
      'KRW-ENS': '이더리움네임서비스',
      'KRW-SOL': '솔라나',
      'KRW-CTC': '크레딧코인',
      'KRW-TRX': '트론',
      # 중형 알트코인
      'KRW-AVAX': '아발란체',
      'KRW-SHIB': '시바이누',
      'KRW-SNT': '스테이터스네트워크토큰',
      'KRW-BTT': '비트토렌트',
      'KRW-XLM': '스텔라루멘',
      # 소형 알트코인
      'KRW-DOGE': '도지코인',
      'KRW-THETA': '세타토큰',
      'KRW-HBAR': '헤데라',
      'KRW-OMNI': '옴니네트워크',
      'KRW-ALGO': '알고랜드',
      # 한국 인기 코인
      'KRW-T': '쓰레스홀드',
      'KRW-ONDO': '온도',
      'KRW-TT': '썬더코어',
      'KRW-CVC': '시빅',
      'KRW-TOKAMAK': '토카막네트워크',
      # DeFi & 신규 코인
      'KRW-IOTA': '아이오타',
      'KRW-AQT': '알파쿼크',
      'KRW-SUI': '수이',
      'KRW-IQ': '아이큐',
      'KRW-XEC': '이캐시',
      'KRW-MTL': '메탈',
      'KRW-PUNDIX': '펀디엑스',
      'KRW-PYTH': '피스네트워크',
      'KRW-KAVA': '카바',
      'KRW-A': '아놀드',
      'KRW-BAT': '베이직어텐션토큰',
      'KRW-ARB': '아비트럼',
      'KRW-WAXP': '왁스',
      'KRW-SAND': '샌드박스',
      'KRW-XTZ': '테조스',
      'KRW-BORA': '보라',
      'KRW-AERGO': '아르고',
      'KRW-NEO': '네오',
      'KRW-EGLD': '멀티버스엑스',
      'KRW-ATOM': '코스모스',
      'KRW-BIGTIME': '빅타임',
      'KRW-ZIL': '질리카',
      'KRW-VET': '비체인',
      'KRW-ELF': '엘프',
      'KRW-DRIFT': '드리프트',
      'KRW-MASK': '마스크네트워크',
      'KRW-NEAR': '니어프로토콜',
      'KRW-G': '그래비티',
      'KRW-SXP': '스와이프',
      'KRW-BEAM': '빔',
      'KRW-POLYX': '폴리매쉬',
      'KRW-ATH': '아토스',
      'KRW-HIVE': '하이브',
      'KRW-QTUM': '퀀텀',
      'KRW-TFUEL': '세타퓨엘',
      'KRW-VANA': '바나',
      'KRW-AGLD': '어드벤처골드',
      'KRW-IOST': '아이오에스티',
      'KRW-MLK': '밀크',
      'KRW-STG': '스타게이트',
      'KRW-SC': '시아코인',
      'KRW-APT': '앱토스',
      'KRW-SAFE': '세이프',
      'KRW-BLAST': '블라스트',
      'KRW-ME': '미미르'
    }

    # 모니터링 대상 코인 (업비트 원화 마켓)
    self.watchlist = [
      # 메이저 코인
      'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT',
      # 대형 알트코인
      'KRW-LINK', 'KRW-ENS', 'KRW-SOL', 'KRW-CTC', 'KRW-TRX',
      # 중형 알트코인
      'KRW-AVAX', 'KRW-SHIB', 'KRW-SNT', 'KRW-BTT', 'KRW-XLM',
      # 소형 알트코인
      'KRW-DOGE', 'KRW-THETA', 'KRW-HBAR', 'KRW-OMNI', 'KRW-ALGO',
      # 한국 인기 코인
      'KRW-T', 'KRW-ONDO', 'KRW-TT', 'KRW-CVC', 'KRW-TOKAMAK',
      # DeFi & 신규 코인
      'KRW-IOTA', 'KRW-AQT', 'KRW-SUI', 'KRW-IQ', 'KRW-XEC',
      'KRW-MTL', 'KRW-PUNDIX', 'KRW-PYTH', 'KRW-KAVA', 'KRW-A',
      'KRW-BAT', 'KRW-ARB', 'KRW-WAXP', 'KRW-SAND', 'KRW-XTZ',
      'KRW-BORA', 'KRW-AERGO', 'KRW-NEO', 'KRW-EGLD', 'KRW-ATOM',
      'KRW-BIGTIME', 'KRW-ZIL', 'KRW-VET', 'KRW-ELF', 'KRW-DRIFT',
      'KRW-MASK', 'KRW-NEAR', 'KRW-G', 'KRW-SXP', 'KRW-BEAM',
      'KRW-POLYX', 'KRW-ATH', 'KRW-HIVE', 'KRW-QTUM', 'KRW-TFUEL',
      'KRW-VANA', 'KRW-AGLD', 'KRW-IOST', 'KRW-MLK', 'KRW-STG',
      'KRW-SC', 'KRW-APT', 'KRW-SAFE', 'KRW-BLAST', 'KRW-ME'
    ]

    # 텔레그램 설정
    self.telegram_bot_token = telegram_bot_token
    self.telegram_chat_id = telegram_chat_id
    self.telegram_app = None
    self.telegram_running = False
    if self.telegram_bot_token:
      try:
        self.telegram_app = Application.builder().token(self.telegram_bot_token).build()
        self.telegram_app.add_handler(CommandHandler("start", self.start_command))
        self.telegram_app.add_handler(CommandHandler("ticker", self.ticker_command))
        self.telegram_app.add_handler(CommandHandler("status", self.status_command))
        self.logger.info("✅ Telegram bot handlers added successfully")
      except Exception as e:
        self.logger.error(f"❌ Telegram bot initialization failed: {e}")
        self.telegram_app = None

    # 기술적 지표 설정
    self.bb_period = 20
    self.bb_std_multiplier = 2.0
    self.rsi_period = 14
    self.rsi_overbought = 70
    self.volatility_lookback = 50
    self.volatility_threshold = 0.2

    # 알림 설정
    self.last_alerts = {}  # 중복 알림 방지
    self.alert_cooldown = 3600  # 1시간 쿨다운
    self.last_signal_time = None

    # Heartbeat 설정
    self.heartbeat_interval = 3600  # 1시간
    self.last_heartbeat = datetime.now()
    self.heartbeat_thread = None
    self.scan_count = 0
    self.total_signals_sent = 0
    self.is_monitoring = False
    self.monitor_thread = None
    self.start_time = None

  async def start_command(self, update, context):
    """Handle /start command."""
    try:
      welcome_message = (
        "🤖 <b>업비트 Volatility Bollinger Bot</b>\n\n"
        "📊 사용 가능한 명령어:\n"
        "• /ticker &lt;symbol&gt; - 코인 분석 (예: /ticker BTC, /ticker btc)\n"
        "• /status - 모니터링 상태 확인\n"
        "• /start - 이 도움말 보기\n\n"
        f"🔍 모니터링 상태: {'🟢 실행중' if self.is_monitoring else '🔴 중지됨'}\n"
        f"📈 감시 코인: {len(self.watchlist)}개\n"
        f"📱 총 알림 발송: {self.total_signals_sent}개\n\n"
        "💡 <b>예시:</b> /ticker BTC 또는 /ticker eth"
      )
      await update.message.reply_text(welcome_message, parse_mode='HTML')
      self.logger.info(f"Sent welcome message to user {update.effective_user.id}")
    except Exception as e:
      self.logger.error(f"Error in start_command: {e}")
      await update.message.reply_text("죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.")

  async def ticker_command(self, update, context):
    """Handle /ticker command to analyze a specific crypto."""
    try:
      self.logger.info(f"Received ticker command from user {update.effective_user.id}: {context.args}")
      if not context.args:
        await update.message.reply_text(
            "❌ 코인 심볼을 입력해주세요.\n\n"
            "💡 <b>사용법:</b> /ticker &lt;심볼&gt;\n"
            "📊 <b>예시:</b>\n"
            "• /ticker BTC\n"
            "• /ticker eth\n"
            "• /ticker XRP",
            parse_mode='HTML'
        )
        return

      ticker_input = context.args[0].upper().strip()
      if not ticker_input.startswith('KRW-'):
        ticker = f"KRW-{ticker_input}"
      else:
        ticker = ticker_input

      self.logger.info(f"Processing analysis for ticker: {ticker}")
      progress_message = await update.message.reply_text(
          f"🔍 <b>{ticker} 분석 중...</b>\n⏳ 잠시만 기다려주세요...",
          parse_mode='HTML'
      )

      signals = self.check_signals(ticker)
      if not signals:
        await progress_message.edit_text(
            f"❌ <b>{ticker} 데이터를 가져올 수 없습니다</b>\n\n"
            "💡 코인 심볼이 올바른지 확인해주세요.\n"
            "📊 인기 코인: BTC, ETH, XRP, ADA, DOT",
            parse_mode='HTML'
        )
        return

      message = self.format_analysis_message(signals)
      await progress_message.edit_text(message, parse_mode='HTML')
      self.logger.info(f"✅ Sent analysis for {ticker} via Telegram command")
    except Exception as e:
      self.logger.error(f"❌ Error analyzing ticker in command: {e}")
      try:
        await update.message.reply_text(
            f"❌ <b>코인 분석 중 오류 발생</b>\n\n"
            f"오류: {str(e)}\n\n"
            "💡 다시 시도하거나 코인 심볼을 확인해주세요.",
            parse_mode='HTML'
        )
      except:
        pass

  async def status_command(self, update, context):
    """Handle /status command to show monitoring status."""
    try:
      current_time = datetime.now()
      uptime = current_time - self.start_time if self.start_time else timedelta(0)
      uptime_str = str(uptime).split('.')[0]
      last_signal_str = "없음"
      if self.last_signal_time:
        time_diff = current_time - self.last_signal_time
        if time_diff.days > 0:
          last_signal_str = f"{time_diff.days}일 전"
        elif time_diff.seconds > 3600:
          last_signal_str = f"{time_diff.seconds // 3600}시간 전"
        elif time_diff.seconds > 60:
          last_signal_str = f"{time_diff.seconds // 60}분 전"
        else:
          last_signal_str = "1분 이내"

      status_message = f"""📊 <b>업비트 모니터링 상태</b>

🔄 상태: {'🟢 실행중' if self.is_monitoring else '🔴 중지됨'}
⏱️ 가동 시간: {uptime_str}
🇰🇷 한국 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}

🟢 <b>24시간 거래 (코인 마켓)</b>

📈 <b>통계:</b>
   🔍 총 스캔: {self.scan_count}회
   📱 알림 발송: {self.total_signals_sent}개
   📊 감시 코인: {len(self.watchlist)}개
   ⏰ 스캔 간격: 5분
   🎯 최근 신호: {last_signal_str}

💡 <b>명령어:</b>
   /ticker &lt;심볼&gt; - 코인 분석
   /status - 상태 확인
   /start - 도움말"""
      await update.message.reply_text(status_message, parse_mode='HTML')
      self.logger.info(f"Sent status to user {update.effective_user.id}")
    except Exception as e:
      self.logger.error(f"Error in status_command: {e}")
      await update.message.reply_text("❌ 상태 조회 중 오류가 발생했습니다. 다시 시도해주세요.")

  def format_analysis_message(self, signals: Dict) -> str:
    """Format analysis message for Telegram command."""
    try:
      symbol = signals['symbol']
      korean_name = self.ticker_to_korean.get(symbol, symbol)
      price = signals['price']
      rsi = signals['rsi']
      bb_pos = signals['bb_position']
      bb_squeeze = signals.get('bb_squeeze', False)
      volume_ratio = signals.get('volume_ratio', 1.0)
      squeeze_breakout = signals.get('squeeze_breakout', False)
      timestamp = signals['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
      buy_signal = signals['buy_signal']
      sell_50_signal = signals['sell_50_signal']
      sell_all_signal = signals['sell_all_signal']

      if rsi >= 70:
        rsi_status = "🔥 과매수"
      elif rsi <= 30:
        rsi_status = "❄️ 과매도"
      else:
        rsi_status = "⚖️ 중립"

      if bb_pos >= 0.8:
        bb_status = "🔴 상단밴드"
      elif bb_pos <= 0.2:
        bb_status = "🟢 하단밴드"
      else:
        bb_status = "🟡 중간영역"

      signals_list = []
      if buy_signal:
        signals_list.append("🚀 매수")
      if sell_50_signal:
        signals_list.append("💡 50% 매도")
      if sell_all_signal:
        signals_list.append("🔴 전량 매도")

      signals_text = " | ".join(signals_list) if signals_list else "📊 신호 없음"

      message = (
        f"📈 <b>분석: {korean_name}</b> ({symbol})\n\n"
        f"💰 <b>현재가:</b> {price:,.0f}원\n"
        f"📊 <b>RSI:</b> {rsi:.1f} ({rsi_status})\n"
        f"📍 <b>BB 위치:</b> {bb_pos:.2f} ({bb_status})\n"
        f"🔥 <b>변동성 압축:</b> {'✅ 활성' if bb_squeeze else '❌ 비활성'}\n"
        f"⚡ <b>브레이크아웃:</b> {'✅ 감지' if squeeze_breakout else '❌ 없음'}\n"
        f"📊 <b>거래량:</b> {volume_ratio:.1f}x\n\n"
        f"🎯 <b>신호:</b> {signals_text}\n\n"
        f"⏰ <b>분석 시간:</b> {timestamp}\n\n"
        f"💡 <b>볼린저 스퀴즈 전략:</b>\n"
        f"• 변동성 압축 → 밴드 브레이크아웃 시 매수\n"
        f"• BB 상단(85%) 근처에서 50% 익절\n"
        f"• BB 하단(15%) 또는 RSI<30에서 전량매도"
      )
      return message
    except Exception as e:
      self.logger.error(f"Error formatting analysis message: {e}")
      return f"❌ {signals.get('symbol', 'unknown')} 분석 메시지 생성 중 오류 발생"

  def send_telegram_alert(self, message: str, parse_mode: str = 'HTML'):
    """텔레그램 알림 전송"""
    if not self.telegram_bot_token or not self.telegram_chat_id:
      self.logger.info(f"Telegram Alert (not sent, no token/chat_id): {message}")
      return False

    message = re.sub(r'<symbol>', '<b>', message, flags=re.IGNORECASE)
    message = re.sub(r'</symbol>', '</b>', message, flags=re.IGNORECASE)
    self.logger.debug(f"Sending Telegram message: {message}")

    url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
    payload = {
      'chat_id': self.telegram_chat_id,
      'text': message,
      'parse_mode': parse_mode
    }

    try:
      response = requests.post(url, data=payload, timeout=10)
      if response.status_code == 200:
        self.logger.info("텔레그램 알림 전송 성공")
        return True
      else:
        self.logger.error(f"텔레그램 전송 실패: {response.text}")
        return False
    except Exception as e:
      self.logger.error(f"텔레그램 전송 오류: {e}")
      return False

  def send_heartbeat(self):
    """Heartbeat 메시지 전송"""
    if not self.telegram_bot_token:
      return

    current_time = datetime.now()
    uptime = current_time - self.start_time if self.start_time else timedelta(0)
    uptime_str = str(uptime).split('.')[0]
    last_signal_str = "없음"
    if self.last_signal_time:
      time_diff = current_time - self.last_signal_time
      if time_diff.days > 0:
        last_signal_str = f"{time_diff.days}일 전"
      elif time_diff.seconds > 3600:
        last_signal_str = f"{time_diff.seconds // 3600}시간 전"
      elif time_diff.seconds > 60:
        last_signal_str = f"{time_diff.seconds // 60}분 전"
      else:
        last_signal_str = "1분 이내"

    hour = current_time.hour
    if 6 <= hour < 12:
      time_emoji = "🌅"
    elif 12 <= hour < 18:
      time_emoji = "☀️"
    elif 18 <= hour < 22:
      time_emoji = "🌆"
    else:
      time_emoji = "🌙"

    heartbeat_message = f"""{time_emoji} <b>Heartbeat - 업비트 모니터링 정상 가동</b>

🇰🇷 한국 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
⏱️ 가동 시간: {uptime_str}

🟢 <b>24시간 거래 중</b>

📊 <b>통계 정보:</b>
   🔍 총 스캔: {self.scan_count}회
   📱 알림 발송: {self.total_signals_sent}개
   📈 감시 코인: {len(self.watchlist)}개
   ⏰ 스캔 간격: 5분

🎯 <b>최근 활동:</b>
   마지막 신호: {last_signal_str}
   알림 기록: {len(self.last_alerts)}개

✅ <b>상태:</b> 모든 시스템 정상 작동 중
🔄 다음 Heartbeat: 1시간 후"""
    if self.send_telegram_alert(heartbeat_message):
      self.logger.info(f"💓 Heartbeat 전송 완료 - 가동시간: {uptime_str}")
      self.last_heartbeat = current_time
    else:
      self.logger.error("💔 Heartbeat 전송 실패")

  def start_heartbeat(self):
    """Heartbeat 스레드 시작"""
    if self.heartbeat_thread and self.heartbeat_thread.is_alive():
      return

    self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
    self.heartbeat_thread.start()
    self.logger.info(f"💓 Heartbeat 스레드 시작 - {self.heartbeat_interval}초 간격")

  def _heartbeat_loop(self):
    """Heartbeat 루프"""
    while self.is_monitoring:
      try:
        time.sleep(self.heartbeat_interval)
        if self.is_monitoring:
          self.send_heartbeat()
      except Exception as e:
        self.logger.error(f"💔 Heartbeat 루프 오류: {e}")
        time.sleep(60)

  def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 계산"""
    if len(data) < max(self.bb_period, self.rsi_period, self.volatility_lookback):
      return data

    if 'close' not in data.columns:
      data.columns = ['open', 'high', 'low', 'close', 'volume']

    data['SMA'] = data['close'].rolling(window=self.bb_period).mean()
    data['STD'] = data['close'].rolling(window=self.bb_period).std()
    data['Upper_Band'] = data['SMA'] + (data['STD'] * self.bb_std_multiplier)
    data['Lower_Band'] = data['SMA'] - (data['STD'] * self.bb_std_multiplier)
    data['Band_Width'] = (data['Upper_Band'] - data['Lower_Band']) / data['SMA']
    data['Volatility_Squeeze'] = data['Band_Width'] < data['Band_Width'].rolling(
        self.volatility_lookback).quantile(self.volatility_threshold)
    data['BB_Position'] = (data['close'] - data['Lower_Band']) / (
        data['Upper_Band'] - data['Lower_Band'])
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Buy_Signal'] = (data['RSI'] > self.rsi_overbought) & (data['Volatility_Squeeze'])
    data['Sell_50_Signal'] = (data['BB_Position'] >= 0.8) | (abs(data['BB_Position'] - 0.5) <= 0.1)
    data['Sell_All_Signal'] = data['BB_Position'] <= 0.1
    return data

  def get_crypto_data(self, symbol: str, count: int = 100) -> Optional[pd.DataFrame]:
    """업비트에서 코인 데이터 가져오기"""
    try:
      data = pyupbit.get_ohlcv(symbol, interval="day", count=count)
      if data is None or data.empty:
        self.logger.warning(f"No data found for {symbol}")
        return None
      if len(data) < self.volatility_lookback:
        self.logger.warning(f"Insufficient data for {symbol}")
        return None
      return data
    except Exception as e:
      self.logger.error(f"Error fetching data for {symbol}: {e}")
      return None

  def check_signals(self, symbol: str) -> Dict:
    """신호 확인 (볼린저 스퀴즈 전략)"""
    try:
      data = self.get_crypto_data(symbol)
      if data is None or len(data) < 50:  # 충분한 데이터 필요
        return {}

      # 볼린거 밴드 계산
      data['SMA'] = data['close'].rolling(20).mean()
      data['STD'] = data['close'].rolling(20).std()
      data['Upper_Band'] = data['SMA'] + (data['STD'] * 2.0)
      data['Lower_Band'] = data['SMA'] - (data['STD'] * 2.0)
      data['Band_Width'] = (data['Upper_Band'] - data['Lower_Band']) / data['SMA']

      # 스퀴즈 감지 (최근 20일 중 최소 밴드폭의 110% 이하)
      data['BB_Squeeze'] = data['Band_Width'] < data['Band_Width'].rolling(20).min() * 1.1
      data['BB_Position'] = (data['close'] - data['Lower_Band']) / (data['Upper_Band'] - data['Lower_Band'])

      # RSI
      delta = data['close'].diff()
      gain = (delta.where(delta > 0, 0)).rolling(14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
      rs = gain / loss
      data['RSI'] = 100 - (100 / (1 + rs))

      # 거래량 비율
      data['Volume_MA'] = data['volume'].rolling(20).mean() if 'volume' in data.columns else 1
      data['Volume_Ratio'] = data['volume'] / data['Volume_MA'] if 'volume' in data.columns else 1

      latest = data.iloc[-1]
      prev = data.iloc[-2] if len(data) > 1 else latest

      # 스퀴즈 브레이크아웃 감지
      squeeze_breakout = (
          prev['BB_Squeeze'] and  # 이전에 스퀴즈 상태였고
          (latest['close'] > latest['Upper_Band'] or  # 상단 돌파 또는
           latest['close'] < latest['Lower_Band']) and  # 하단 이탈
          latest['Volume_Ratio'] > 1.2  # 거래량 증가
      )

      signals = {
        'symbol': symbol,
        'price': float(latest['close']),
        'rsi': float(latest['RSI']),
        'bb_position': float(latest['BB_Position']),
        'band_width': float(latest['Band_Width']),
        'bb_squeeze': bool(latest['BB_Squeeze']),
        'volume_ratio': float(latest['Volume_Ratio']),
        'squeeze_breakout': squeeze_breakout,
        'buy_signal': squeeze_breakout and latest['close'] > latest['Upper_Band'] and 50 < latest['RSI'] < 80,
        'sell_50_signal': latest['BB_Position'] >= 0.85,
        'sell_all_signal': latest['BB_Position'] <= 0.15 or latest['RSI'] < 30,
        'timestamp': latest.name
      }

      return signals

    except Exception as e:
      self.logger.error(f"Error checking signals for {symbol}: {e}")
      return {}

  def should_send_alert(self, symbol: str, signal_type: str) -> bool:
    """알림 쿨다운 확인"""
    key = f"{symbol}_{signal_type}"
    current_time = time.time()
    if key in self.last_alerts:
      if current_time - self.last_alerts[key] < self.alert_cooldown:
        return False
    self.last_alerts[key] = current_time
    return True

  def format_alert_message(self, signals: Dict, signal_type: str) -> str:
    """알림 메시지 포맷팅 (볼린저 스퀴즈 전략)"""
    symbol = signals['symbol']
    korean_name = self.ticker_to_korean.get(symbol, symbol)
    price = signals['price']
    rsi = signals['rsi']
    bb_pos = signals['bb_position']
    volume_ratio = signals.get('volume_ratio', 1.0)
    timestamp = signals['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    if signal_type == 'buy':
      direction = "상승" if bb_pos > 0.5 else "하락"
      message = f"""🚀 <b>볼린저 스퀴즈 브레이크아웃!</b>

코인: <b>{korean_name}</b> ({symbol})
현재가: <b>{price:,.0f}원</b>
브레이크아웃 방향: <b>{direction}</b>
RSI: <b>{rsi:.1f}</b>
BB 위치: <b>{bb_pos:.2f}</b>
거래량 비율: <b>{volume_ratio:.1f}x</b>
시간: {timestamp}

⚡ 변동성 압축 후 폭발적 움직임 시작!"""

    elif signal_type == 'sell_50':
      message = f"""💡 <b>50% 익절 신호!</b>

코인: <b>{korean_name}</b> ({symbol})
현재가: <b>{price:,.0f}원</b>
BB 위치: <b>{bb_pos:.2f}</b> (상단 근접)
시간: {timestamp}

📈 첫 번째 수익 구간 도달!"""

    else:  # sell_all
      reason = "손절" if rsi < 30 else "하단 이탈"
      message = f"""🔴 <b>전량 매도 신호!</b>

코인: <b>{korean_name}</b> ({symbol})
현재가: <b>{price:,.0f}원</b>
신호 사유: <b>{reason}</b>
BB 위치: <b>{bb_pos:.2f}</b>
RSI: <b>{rsi:.1f}</b>
시간: {timestamp}

⚠️ 추세 전환 또는 리스크 관리 시점!"""

    return message

  def process_signals(self, signals: Dict) -> bool:
    """신호 처리 및 알림"""
    if not signals:
      return False
    symbol = signals['symbol']
    alert_sent = False
    if signals['buy_signal'] and self.should_send_alert(symbol, 'buy'):
      message = self.format_alert_message(signals, 'buy')
      if self.send_telegram_alert(message):
        self.logger.info(f"🚀 매수 신호 알림 전송: {symbol}")
        self.total_signals_sent += 1
        self.last_signal_time = datetime.now()
        alert_sent = True
    if signals['sell_50_signal'] and self.should_send_alert(symbol, 'sell_50'):
      message = self.format_alert_message(signals, 'sell_50')
      if self.send_telegram_alert(message):
        self.logger.info(f"💡 50% 매도 신호 알림 전송: {symbol}")
        self.total_signals_sent += 1
        self.last_signal_time = datetime.now()
        alert_sent = True
    if signals['sell_all_signal'] and self.should_send_alert(symbol, 'sell_all'):
      message = self.format_alert_message(signals, 'sell_all')
      if self.send_telegram_alert(message):
        self.logger.info(f"🔴 전량 매도 신호 알림 전송: {symbol}")
        self.total_signals_sent += 1
        self.last_signal_time = datetime.now()
        alert_sent = True
    return alert_sent

  def scan_single_crypto(self, symbol: str):
    """단일 코인 스캔"""
    try:
      signals = self.check_signals(symbol)
      if signals:
        self.process_signals(signals)
        if any([signals.get('buy_signal'), signals.get('sell_50_signal'), signals.get('sell_all_signal')]):
          self.logger.info(
              f"{symbol}: Price={signals['price']:,.0f}원, RSI={signals['rsi']:.1f}, BB_Pos={signals['bb_position']:.2f}")
    except Exception as e:
      self.logger.error(f"Error scanning {symbol}: {e}")

  def _scan_all_cryptos_auto(self) -> int:
    """전체 코인 자동 스캔"""
    signals_found = 0
    failed_cryptos = []
    for i, symbol in enumerate(self.watchlist):
      try:
        if (i + 1) % 10 == 0:
          self.logger.info(
              f"   진행률: {i + 1}/{len(self.watchlist)} ({(i + 1) / len(self.watchlist) * 100:.0f}%)")
        signals = self.check_signals(symbol)
        if signals:
          if self.process_signals(signals):
            signals_found += 1
        time.sleep(0.2)
      except Exception as e:
        self.logger.error(f"❌ {symbol} 스캔 오류: {e}")
        failed_cryptos.append(symbol)
        continue
    if failed_cryptos:
      self.logger.warning(f"⚠️ 스캔 실패 코인: {', '.join(failed_cryptos)}")
    return signals_found

  def _run_telegram_bot(self):
    """Run Telegram bot in a separate thread."""
    try:
      self.logger.info("🤖 Starting Telegram bot polling...")
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      self.telegram_app.run_polling(
          poll_interval=1.0,
          timeout=10,
          drop_pending_updates=True,
          stop_signals=None
      )
    except Exception as e:
      self.logger.error(f"❌ Telegram bot error: {e}")
      self.telegram_running = False
      if self.is_monitoring:
        self.logger.info("🔄 Attempting to restart Telegram bot in 30 seconds...")
        time.sleep(30)
        if self.is_monitoring and not self.telegram_running:
          self.telegram_running = True
          self._run_telegram_bot()

  def _auto_monitoring_loop(self, scan_interval: int):
    """자동 모니터링 루프"""
    while self.is_monitoring:
      try:
        self.scan_count += 1
        current_time = datetime.now()
        self.logger.info(
            f"📊 스캔 #{self.scan_count} 시작 - {current_time.strftime('%H:%M:%S')}")
        self.logger.info(f"   🟢 24시간 거래 중 (코인 마켓)")
        signals_found = self._scan_all_cryptos_auto()
        if signals_found > 0:
          self.logger.info(f"🎯 {signals_found}개 신호 발견 및 알림 전송 완료")
        else:
          self.logger.info("📈 신호 없음 - 모니터링 계속")
        if self.scan_count % 5 == 0:
          self._send_status_summary(self.scan_count)
        next_scan_time = (
            current_time + timedelta(seconds=scan_interval)).strftime('%H:%M:%S')
        self.logger.info(f"   ⏰ 다음 스캔: {next_scan_time}")
        time.sleep(scan_interval)
      except Exception as e:
        self.logger.error(f"❌ 모니터링 루프 오류: {e}")
        self.logger.info("🔄 30초 후 재시도...")
        time.sleep(30)

  def _send_status_summary(self, scan_count: int):
    """상태 요약 전송 (5회마다)"""
    if not self.telegram_bot_token:
      return
    current_time = datetime.now()
    uptime = current_time - self.start_time if self.start_time else timedelta(0)
    summary_message = f"""📊 <b>모니터링 상태 요약</b>

🔢 스캔 횟수: {scan_count}회
⏰ 현재 시간: {current_time.strftime('%H:%M:%S')}
🕐 실행 시간: {str(uptime).split('.')[0]}
📈 감시 코인: {len(self.watchlist)}개
🎯 알림 전송: {self.total_signals_sent}개

✅ 시스템 정상 작동 중"""
    self.send_telegram_alert(summary_message)

  def start_monitoring(self, scan_interval: int = 300):
    """자동 모니터링 시작"""
    if self.is_monitoring:
      self.logger.warning("모니터링이 이미 실행 중입니다.")
      return
    self.is_monitoring = True
    self.start_time = datetime.now()
    self.scan_count = 0
    self.total_signals_sent = 0
    self.last_signal_time = None
    self.logger.info(f"🚀 자동 모니터링 시작 (스캔 간격: {scan_interval}초)")
    if self.telegram_app and not self.telegram_running:
      self.telegram_running = True
      self.telegram_thread = threading.Thread(target=self._run_telegram_bot, daemon=True)
      self.telegram_thread.start()
      self.logger.info("✅ Telegram bot thread started")
    self.start_heartbeat()
    if self.telegram_bot_token:
      start_message = f"""🤖 <b>업비트 모니터링 시작</b>

📊 감시 코인: {len(self.watchlist)}개 (업비트 원화 마켓)
⏰ 스캔 간격: {scan_interval}초 ({scan_interval // 60}분)
💓 Heartbeat: 매시간마다
🕐 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}

🎯 변동성 볼린저 밴드 전략 활성화
⚡ 실시간 알림이 즉시 전송됩니다
💓 시스템 상태 업데이트는 매시간마다

📱 <b>명령어:</b>
• /ticker &lt;심볼&gt; - 코인 분석
• /status - 모니터링 상태
• /start - 도움말

💡 <b>예시:</b> /ticker BTC"""
      self.send_telegram_alert(start_message)
    self.monitor_thread = threading.Thread(target=self._auto_monitoring_loop, args=(scan_interval,), daemon=False)  # Changed daemon to False
    self.monitor_thread.start()
    self.logger.info("✅ 자동 모니터링 스레드가 시작되었습니다.")
    # Keep main thread alive by joining the monitoring thread
    try:
      self.monitor_thread.join()
    except KeyboardInterrupt:
      self.stop_monitoring()
      self.logger.info("✅ 모니터링이 사용자 요청으로 중지되었습니다.")

  def stop_monitoring(self):
    """모니터링 중지"""
    if not self.is_monitoring:
      self.logger.warning("모니터링이 실행되고 있지 않습니다.")
      return
    self.is_monitoring = False
    self.telegram_running = False
    if self.monitor_thread:
      self.monitor_thread.join(timeout=10)
    if self.telegram_app:
      try:
        asyncio.run(self.telegram_app.stop())
      except Exception as e:
        self.logger.warning(f"Error stopping Telegram bot: {e}")
    if self.telegram_bot_token and self.start_time:
      end_time = datetime.now()
      uptime = end_time - self.start_time
      stop_message = f"""⏹️ <b>업비트 모니터링 중지</b>

🕐 중지 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
⏱️ 총 가동시간: {str(uptime).split('.')[0]}
🔢 총 스캔: {self.scan_count}회
🎯 총 알림: {self.total_signals_sent}개

✅ 모니터링이 안전하게 중지되었습니다."""
      self.send_telegram_alert(stop_message)
    self.logger.info("✅ 모니터링이 중지되었습니다.")

  def get_monitoring_statistics(self) -> Dict:
    """모니터링 통계 조회"""
    uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
    return {
      'is_running': self.is_monitoring,
      'watchlist_count': len(self.watchlist),
      'uptime_seconds': uptime.total_seconds(),
      'uptime_formatted': str(uptime).split('.')[0],
      'total_alerts': self.total_signals_sent,
      'scan_count': self.scan_count,
      'telegram_configured': bool(self.telegram_bot_token and self.telegram_chat_id),
      'last_heartbeat': self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S') if self.last_heartbeat else None,
      'last_signal_time': self.last_signal_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_signal_time else None
    }

  def get_current_status(self) -> Dict:
    """현재 상태 조회"""
    return {
      'is_monitoring': self.is_monitoring,
      'watchlist_count': len(self.watchlist),
      'last_alerts_count': len(self.last_alerts),
      'telegram_configured': bool(self.telegram_bot_token and self.telegram_chat_id),
      'scan_count': self.scan_count,
      'total_signals_sent': self.total_signals_sent
    }

  def add_to_watchlist(self, symbols: List[str]):
    """감시 목록에 코인 추가"""
    for symbol in symbols:
      if not symbol.startswith('KRW-'):
        symbol = f"KRW-{symbol}"
      if symbol not in self.watchlist:
        self.watchlist.append(symbol)
        self.logger.info(f"Added {symbol} to watchlist")

  def remove_from_watchlist(self, symbols: List[str]):
    """감시 목록에서 코인 제거"""
    for symbol in symbols:
      if not symbol.startswith('KRW-'):
        symbol = f"KRW-{symbol}"
      if symbol in self.watchlist:
        self.watchlist.remove(symbol)
        self.logger.info(f"Removed {symbol} from watchlist")

  def get_market_overview(self) -> pd.DataFrame:
    """시장 개요 조회"""
    overview_data = []
    self.logger.info("Generating market overview...")
    for symbol in self.watchlist:
      try:
        signals = self.check_signals(symbol)
        if signals:
          overview_data.append({
            'Symbol': symbol,
            'Price': f"{signals['price']:,.0f}원",
            'RSI': f"{signals['rsi']:.1f}",
            'BB_Position': f"{signals['bb_position']:.2f}",
            'Vol_Squeeze': '🔥' if signals['volatility_squeeze'] else '❄️',
            'Buy_Signal': '🚀' if signals['buy_signal'] else '',
            'Sell_50': '💡' if signals['sell_50_signal'] else '',
            'Sell_All': '🔴' if signals['sell_all_signal'] else ''
          })
      except Exception as e:
        self.logger.error(f"Error in overview for {symbol}: {e}")
    return pd.DataFrame(overview_data)

  def manual_scan(self, symbol: str = None):
    """수동 스캔"""
    if symbol:
      if not symbol.startswith('KRW-'):
        symbol = f"KRW-{symbol}"
      self.logger.info(f"Manual scan for {symbol}")
      self.scan_single_crypto(symbol)
    else:
      self.logger.info("Manual scan for all cryptos")
      self._scan_all_cryptos_auto()

  def test_telegram_connection(self):
    """텔레그램 연결 테스트"""
    test_message = f"""🧪 <b>업비트 봇 연결 테스트</b>

텔레그램 봇이 정상적으로 작동합니다!
테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 알림 수신 준비 완료
💓 Heartbeat 기능 활성화됨
🟢 24시간 거래 모니터링
📬 Use /ticker <symbol> to analyze a crypto (e.g., /ticker BTC or /ticker eth)"""
    success = self.send_telegram_alert(test_message)
    if success:
      self.logger.info("Telegram connection test successful")
    else:
      self.logger.error("Telegram connection test failed")
    return success

def main():
  """메인 실행 함수"""
  TELEGRAM_BOT_TOKEN = os.getenv('UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN')
  TELEGRAM_CHAT_ID = os.getenv('UPBIT_BOLLINGER_TELEGRAM_CHAT_ID')
  monitor = UpbitRealTimeVolatilityMonitor(
      telegram_bot_token=TELEGRAM_BOT_TOKEN,
      telegram_chat_id=TELEGRAM_CHAT_ID
  )
  print("=== 업비트 실시간 변동성 폭파 모니터링 시스템 ===")
  print("💓 Heartbeat 기능: 1시간마다 상태 알림")
  print("🟢 24시간 거래 (코인 마켓)")
  print("📬 Use /ticker <symbol> to analyze a crypto (e.g., /ticker BTC or /ticker eth)")
  if monitor.telegram_bot_token:
    monitor.test_telegram_connection()
  try:
    print("\n현재 시장 개요:")
    overview = monitor.get_market_overview()
    if not overview.empty:
      print(overview.to_string(index=False))
    current_time = datetime.now()
    print(f"\n시장 시간 정보:")
    print(f"🇰🇷 한국 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 거래 상태: 🟢 24시간 거래 중")
    print("\n실시간 모니터링 시작...")
    monitor.start_monitoring(scan_interval=300)  # Changed from run_continuous_monitoring to start_monitoring
  except KeyboardInterrupt:
    print("\n모니터링 종료 중...")
    monitor.stop_monitoring()
    print("모니터링이 종료되었습니다.")
  except Exception as e:
    print(f"오류 발생: {e}")
    monitor.stop_monitoring()

if __name__ == "__main__":
  main()
