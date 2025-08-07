"""
업비트 코인 변동성 폭파 볼린저 밴드 트레이딩 시스템 - 메인 실행 파일

사용법:
    python upbit_main.py --mode backtest    # 백테스트만 실행
    python upbit_main.py --mode monitor     # 실시간 모니터링만 실행
    python upbit_main.py --mode monitor-default  # 백그라운드 모니터링 (기본값)
    python upbit_main.py --mode both        # 백테스트 후 모니터링 실행 (기본값)

텔레그램 설정:
    export UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN="your_bot_token"
    export UPBIT_BOLLINGER_TELEGRAM_CHAT_ID="your_chat_id"
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from upbit_realtime_monitor import UpbitRealTimeVolatilityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
      logging.FileHandler(
          f"upbit_output_files/logs/upbit_monitor_{datetime.now().strftime('%Y%m%d')}.log",
          encoding='utf-8'),
      logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set Korean font (Apple SD Gothic Neo for macOS)
font_name = 'Apple SD Gothic Neo'
font_path = fm.findfont(fm.FontProperties(family=font_name))
if font_path:
  plt.rcParams['font.family'] = font_name
  plt.rcParams['axes.unicode_minus'] = False
  logger.info(f"✅ 한글 폰트 설정: {font_name}")
else:
  logger.warning(f"⚠️ 폰트 {font_name}을 찾을 수 없습니다. 기본 폰트 사용.")
  plt.rcParams['font.family'] = 'sans-serif'


def main():
  parser = argparse.ArgumentParser(description="업비트 변동성 폭파 볼린저 밴드 트레이딩 시스템")
  parser.add_argument('--mode', type=str, default='monitor-default',
                      choices=['monitor-default', 'backtest'],
                      help="실행 모드: monitor-default (실시간 모니터링), backtest (백테스팅)")
  args = parser.parse_args()

  print(
    "🚀==============================================================================🚀")
  print("     업비트 코인 변동성 폭파 볼린거 밴드 트레이딩 시스템")
  print(
    "🚀==============================================================================🚀")
  print(f"⚙️ 실행 모드: {args.mode.upper()}")
  print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  print(f"🐍 Python 버전: {sys.version.split()[0]}")
  print("🟢 24시간 거래: 주말에도 모니터링")
  print(
    "📬 Telegram Commands: Use /ticker to analyze a crypto (e.g., /ticker BTC)")
  print(f"📦 pyupbit 라이브러리: {'설치됨' if 'pyupbit' in sys.modules else '미설치'}")

  # Check Upbit API keys (optional for monitoring)
  access_key = os.getenv('UPBIT_ACCESS_KEY')
  secret_key = os.getenv('UPBIT_SECRET_KEY')
  if not (access_key and secret_key):
    print("⚠️ 업비트 API: 미설정 (공개 API 사용, 제한적)")
    print("💡 더 안정적인 데이터 수집을 위해 API 키 설정을 권장합니다.")
    print("   export UPBIT_ACCESS_KEY='your_access_key'")
    print("   export UPBIT_SECRET_KEY='your_secret_key'")

  print("=" * 80)

  try:
    if args.mode == 'backtest':
      # 백테스트 모드 실행
      print("📊 업비트 코인 백테스트")
      print("=" * 80)

      from upbit_backtest_strategy import UpbitVolatilityBollingerBacktest

      # 초기 자금 설정
      print("💰 초기 자금을 설정하세요:")
      print("1. 1,000,000원 (100만원)")
      print("2. 5,000,000원 (500만원)")
      print("3. 10,000,000원 (1천만원)")
      print("4. 사용자 정의")

      capital_options = {"1": 1000000, "2": 5000000, "3": 10000000}

      try:
        capital_choice = input("\n초기 자금 선택 (1-4, 기본값: 1): ").strip() or "1"

        if capital_choice == "4":
          custom_capital = float(input("사용자 정의 금액 (원): "))
          initial_capital = custom_capital
        else:
          initial_capital = capital_options.get(capital_choice, 1000000)

        print(f"✅ 선택된 초기 자금: {initial_capital:,.0f}원")

      except ValueError:
        print("잘못된 입력입니다. 기본값(1,000,000원)으로 설정합니다.")
        initial_capital = 1000000

      # 투자 전략 선택
      print(f"\n📊 투자 전략을 선택하세요:")
      print("1. 보수적 전략 (안전 우선, RSI 70)")
      print("2. 균형 전략 (적당한 위험, RSI 65)")
      print("3. 공격적 전략 (수익 추구, RSI 60)")

      try:
        strategy_choice = input("\n전략 선택 (1-3, 기본값: 2): ").strip() or "2"
        strategy_map = {"1": "conservative", "2": "balanced", "3": "aggressive"}
        strategy_mode = strategy_map.get(strategy_choice, "balanced")
      except:
        strategy_mode = "balanced"

      # 백테스트 인스턴스 생성
      backtest = UpbitVolatilityBollingerBacktest(
          initial_capital=initial_capital,
          strategy_mode=strategy_mode
      )

      # 백테스트 기간 설정
      days = 1095  # 3년
      print(f"📅 분석 기간: 최근 {days}일 (약 3년)")

      # 코인 수 선택
      print(f"\n📊 분석할 코인 수를 선택하세요:")
      print("1. 5개 코인 (빠름)")
      print("2. 10개 코인 (표준)")
      print("3. 15개 코인")
      print("4. 전체 코인 (시간 오래 걸림)")

      coin_options = {"1": 5, "2": 10, "3": 15, "4": len(backtest.crypto_list)}

      try:
        coin_choice = input("\n코인 수 선택 (1-4, 기본값: 2): ").strip() or "2"
        max_cryptos = coin_options.get(coin_choice, 10)
        print(f"✅ 선택된 코인 수: {max_cryptos}개")
      except:
        max_cryptos = 10

      # 상세 분석 모드 선택
      analysis_options = {
        "1": ("top3", "빠른 분석 (상위 3개 코인 상세분석)"),
        "2": ("top5", "표준 분석 (상위 5개 코인 상세분석)"),
        "3": ("positive", "수익 코인 전체 상세분석"),
        "4": ("all", "전체 코인 상세분석 (매우 오래 걸림)"),
        "5": ("none", "요약만 (상세 분석 없음)")
      }

      print(f"\n📈 상세 분석 모드를 선택하세요:")
      for key, (mode, desc) in analysis_options.items():
        print(f"{key}. {desc}")

      try:
        choice = input(f"\n선택 (1-5, 기본값: 2): ").strip() or "2"
        analysis_mode, description = analysis_options.get(choice,
                                                          ("top5", "표준 분석"))
        print(f"✅ 선택된 분석 모드: {description}")
      except:
        analysis_mode, description = ("top5", "표준 분석")

      if max_cryptos >= 15:
        print(f"⚠️ {max_cryptos}개 코인 분석은 시간이 오래 걸릴 수 있습니다.")

      # 백테스트 실행
      print(f"\n🚀 업비트 코인 백테스트 실행...")
      print(f"📊 {max_cryptos}개 코인 + {description}")

      results = backtest.run_comprehensive_analysis(
          days=days,
          max_cryptos=max_cryptos,
          detailed_analysis=analysis_mode,
          save_charts=True
      )

      if results:
        print(f"\n✅ 백테스트 완료!")

        # 투자 권장사항
        summary_results = results.get('summary_results')
        if summary_results is not None and not summary_results.empty:
          top_performers = summary_results.head(3)
          print(f"\n🏆 투자 추천 코인 (상위 3개):")
          for i, (_, row) in enumerate(top_performers.iterrows()):
            print(f"{i + 1}. {row['Symbol']}: {row['Total_Return(%)']}% 수익률")
        else:
          print("❌ 백테스트 결과가 없습니다.")
      else:
        print("❌ 백테스트 실패")

    elif args.mode == 'monitor-default':
      # 기존 모니터링 코드
      telegram_bot_token = os.getenv('UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN')
      telegram_chat_id = os.getenv('UPBIT_BOLLINGER_TELEGRAM_CHAT_ID')

      print(f"📡 업비트 코인 백그라운드 모니터링 (기본 설정)")
      print("=" * 80)

      monitor = UpbitRealTimeVolatilityMonitor(
          telegram_bot_token=telegram_bot_token,
          telegram_chat_id=telegram_chat_id
      )

      logger.info("업비트 백그라운드 모니터링 시작")
      logger.info("스캔 간격: 300초 (5분)")
      logger.info(
        f"로그 파일: upbit_output_files/logs/upbit_monitor_{datetime.now().strftime('%Y%m%d')}.log")

      print(f"""🎯 백그라운드 모니터링 설정:
   📊 감시 코인: {len(monitor.watchlist)}개 (업비트 원화 마켓)
   ⏰ 스캔 간격: 5분
   📱 텔레그램 알림: {'활성화' if telegram_bot_token else '비활성화'}
   🟢 24시간 거래 모니터링
   📝 로그 파일: upbit_output_files/logs/upbit_monitor_{datetime.now().strftime('%Y%m%d')}.log
   🔄 자동 재시작: 활성화
   🤖 텔레그램 명령어: /ticker, /status, /start""")

      print("=" * 80)
      print("""🚀 업비트 백그라운드 모니터링 시작!
   - 모든 설정이 기본값으로 자동 설정되었습니다
   - 신호 발생시 텔레그램으로 즉시 알림을 전송합니다
   - 텔레그램에서 /ticker 명령어로 개별 코인 분석 가능
   - 5회 스캔마다 상태 요약을 전송합니다
   - 24시간 거래로 주말에도 모니터링합니다
   - 오류 발생시 자동으로 재시작합니다
   - 종료하려면: kill -TERM [PID] 또는 Ctrl+C""")
      print("=" * 80)

      monitor.start_monitoring(scan_interval=300)

      # Keep main thread alive
      while monitor.is_monitoring:
        time.sleep(10)  # Check every 10 seconds
        logger.debug("Main thread checking monitoring status...")

    else:
      logger.error(f"지원하지 않는 모드: {args.mode}")
      print(f"❌ 지원하지 않는 모드: {args.mode}")
      sys.exit(1)

  except KeyboardInterrupt:
    print(f"\n⏹️ 사용자에 의해 프로그램이 중단되었습니다.")
    if 'monitor' in locals():
      monitor.stop_monitoring()
  except Exception as e:
    logger.error(f"모니터링 초기화 실패: {str(e)}", exc_info=True)
    print(f"❌ 프로그램 실행 실패: {str(e)}")
    print("💡 텔레그램 설정이나 네트워크 연결을 확인해주세요.")
    print("📦 pyupbit 라이브러리가 설치되어 있는지 확인해주세요: pip install pyupbit")
    if 'monitor' in locals():
      monitor.stop_monitoring()
    sys.exit(1)
  finally:
    print(f"🏁 프로그램을 종료합니다.")
    print(f"📅 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💖 Happy Trading!")


if __name__ == "__main__":
  main()
