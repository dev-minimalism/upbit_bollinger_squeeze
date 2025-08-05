"""
업비트 코인 변동성 폭파 볼린저 밴드 트레이딩 시스템 - 메인 실행 파일

사용법:
    python main.py --mode backtest    # 백테스트만 실행
    python main.py --mode monitor     # 실시간 모니터링만 실행
    python main.py --mode monitor-default  # 백그라운드 모니터링 (기본값)
    python main.py --mode both        # 백테스트 후 모니터링 실행 (기본값)

텔레그램 설정:
    export UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN="your_bot_token"
    export UPBIT_BOLLINGER_TELEGRAM_CHAT_ID="your_chat_id"
"""

import argparse
import logging
import os
import signal
import sys
from datetime import datetime

# 모듈 import
try:
  from upbit_backtest_strategy import UpbitVolatilityBollingerBacktest
  from upbit_realtime_monitor import UpbitRealTimeVolatilityMonitor
except ImportError as e:
  print(f"❌ 모듈 import 오류: {e}")
  print(
    "📁 upbit_backtest_strategy.py와 upbit_realtime_monitor.py 파일이 같은 디렉토리에 있는지 확인하세요.")
  print("📦 pyupbit 라이브러리 설치 필요: pip install pyupbit")
  sys.exit(1)


# ===================================================================================
# 로깅 설정
# ===================================================================================

def setup_logging():
  """백그라운드 실행을 위한 로깅 설정"""
  log_dir = "upbit_output_files/logs"
  os.makedirs(log_dir, exist_ok=True)

  log_filename = os.path.join(log_dir,
                              f"upbit_monitor_{datetime.now().strftime('%Y%m%d')}.log")

  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(levelname)s - %(message)s',
      handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
      ]
  )

  return logging.getLogger(__name__)


# ===================================================================================
# 백그라운드 모니터링 (기본값)
# ===================================================================================

def run_monitor_default():
  """백그라운드 모니터링 실행 (모든 설정 기본값)"""
  logger = setup_logging()

  print("=" * 80)
  print("📡 업비트 코인 백그라운드 모니터링 (기본 설정)")
  print("=" * 80)

  # 기본 설정값
  telegram_bot_token = os.getenv('UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN')
  telegram_chat_id = os.getenv('UPBIT_BOLLINGER_TELEGRAM_CHAT_ID')
  scan_interval = 300  # 5분 간격

  logger.info("업비트 백그라운드 모니터링 시작")
  logger.info(f"스캔 간격: {scan_interval}초 ({scan_interval // 60}분)")
  logger.info(
    f"로그 파일: upbit_output_files/logs/upbit_monitor_{datetime.now().strftime('%Y%m%d')}.log")

  print(f"🎯 백그라운드 모니터링 설정:")
  print(f"   📊 감시 코인: 30개 (업비트 원화 마켓)")
  print(f"   ⏰ 스캔 간격: 5분")
  print(f"   📱 텔레그램 알림: 활성화")
  print(f"   🟢 24시간 거래 모니터링")
  print(
    f"   📝 로그 파일: upbit_output_files/logs/upbit_monitor_{datetime.now().strftime('%Y%m%d')}.log")
  print(f"   🔄 자동 재시작: 활성화")
  print(f"   🤖 텔레그램 명령어: /ticker, /status, /start")

  # 시그널 핸들러 설정 (graceful shutdown)
  def signal_handler(signum, frame):
    logger.info(f"종료 신호 수신: {signum}")
    print(f"\n⏹️ 모니터링을 안전하게 종료합니다...")
    try:
      if 'monitor' in locals():
        monitor.stop_monitoring()
    except:
      pass
    sys.exit(0)

  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  # 모니터링 시스템 초기화
  try:
    monitor = UpbitRealTimeVolatilityMonitor(
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id
    )

    # 텔레그램 연결 테스트
    if monitor.telegram_bot_token:
      print(f"\n🤖 텔레그램 봇 연결 테스트 중...")
      if monitor.test_telegram_connection():
        print("✅ 텔레그램 연결 성공")
        print("📱 사용 가능한 명령어:")
        print("   • /ticker BTC - 비트코인 분석")
        print("   • /ticker ETH - 이더리움 분석")
        print("   • /status - 모니터링 상태 확인")
        print("   • /start - 도움말 보기")
      else:
        print("⚠️ 텔레그램 연결 실패 - 로그만 출력")

    print(f"\n" + "=" * 80)
    print("🚀 업비트 백그라운드 모니터링 시작!")
    print("   - 모든 설정이 기본값으로 자동 설정되었습니다")
    print("   - 신호 발생시 텔레그램으로 즉시 알림을 전송합니다")
    print("   - 텔레그램에서 /ticker 명령어로 개별 코인 분석 가능")
    print("   - 5회 스캔마다 상태 요약을 전송합니다")
    print("   - 24시간 거래로 주말에도 모니터링합니다")
    print("   - 오류 발생시 자동으로 재시작합니다")
    print("   - 종료하려면: kill -TERM [PID] 또는 Ctrl+C")
    print("=" * 80)

    # 연속 모니터링 실행
    monitor.run_continuous_monitoring(scan_interval)

  except Exception as e:
    logger.error(f"모니터링 초기화 실패: {e}")
    print(f"❌ 모니터링 초기화 실패: {e}")
    print(f"💡 텔레그램 설정이나 네트워크 연결을 확인해주세요.")
    print(f"📦 pyupbit 라이브러리가 설치되어 있는지 확인해주세요: pip install pyupbit")
    sys.exit(1)


# ===================================================================================
# 백테스트 실행
# ===================================================================================

def run_backtest():
  """백테스트 실행"""
  print("=" * 80)
  print("🚀 업비트 코인 변동성 폭파 볼린저 밴드 백테스트")
  print("=" * 80)

  # 초기 자금 설정
  print(f"\n💰 초기 자금을 설정하세요:")
  print("1. 1,000,000원 (100만원)")
  print("2. 5,000,000원 (500만원)")
  print("3. 10,000,000원 (1000만원)")
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
  backtest = UpbitVolatilityBollingerBacktest(initial_capital=initial_capital,
                                              strategy_mode=strategy_mode)

  # 백테스트 기간 설정
  days = 365 * 3  # 3년간 (1095일)

  print(f"📅 분석 기간: 최근 {days}일 (약 3년)")

  # 코인 수 선택
  print(f"\n📊 분석할 코인 수를 선택하세요:")
  print("1. 10개 코인 (빠름)")
  print("2. 15개 코인 (표준)")
  print("3. 20개 코인")
  print("4. 전체 30개 코인 (시간 오래 걸림)")

  crypto_options = {"1": 10, "2": 15, "3": 20, "4": 30}

  max_cryptos = 15
  analysis_mode = "top5"
  description = "표준 분석"
  save_charts = True

  try:
    crypto_choice = input("\n코인 수 선택 (1-4, 기본값: 2): ").strip() or "2"
    max_cryptos = crypto_options.get(crypto_choice, 15)

    print(f"✅ 선택된 코인 수: {max_cryptos}개")

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

    choice = input(f"\n선택 (1-5, 기본값: 2): ").strip() or "2"
    analysis_mode, description = analysis_options.get(choice, ("top5", "표준 분석"))

    print(f"✅ 선택된 분석 모드: {description}")
    print(f"📊 총 {max_cryptos}개 코인 백테스트 + {description}")

    if analysis_mode != "none":
      chart_choice = input(
          "\n차트 저장 방식을 선택하세요 (1: 파일저장, 2: 화면출력, 기본값: 1): ").strip() or "1"
      save_charts = (chart_choice == "1")

      if save_charts:
        print("✅ 차트는 'upbit_output_files/charts/' 폴더에 PNG 파일로 저장됩니다.")
      else:
        print("✅ 차트는 화면에 출력됩니다.")

    if max_cryptos >= 25:
      print(f"⚠️ {max_cryptos}개 코인 분석은 시간이 오래 걸릴 수 있습니다.")
    if analysis_mode == "all":
      print(f"⚠️ 전체 코인 상세분석은 매우 오래 걸립니다.")

    print(f"\n🚀 업비트 코인 백테스트 실행...")
    comprehensive_results = backtest.run_comprehensive_analysis(
        days=days,
        max_cryptos=max_cryptos,
        detailed_analysis=analysis_mode,
        save_charts=save_charts
    )

    if comprehensive_results:
      print(f"\n✅ 백테스트 완료!")
      print(
        f"📊 총 {len(comprehensive_results.get('summary_results', []))}개 코인 분석")
      print(
        f"📈 상세 분석: {len(comprehensive_results.get('detailed_results', []))}개 코인")

      # 투자 권장사항
      summary_results = comprehensive_results.get('summary_results')
      if not summary_results.empty:
        top_performers = summary_results.head(3)
        print(f"\n🏆 투자 추천 코인 (상위 3개):")
        for i, (_, row) in enumerate(top_performers.iterrows()):
          profit_amount = (row['Total_Return(%)'] / 100) * initial_capital
          print(
            f"{i + 1}. {row['Symbol']}: {row['Total_Return(%)']}% 수익률 ({profit_amount:,.0f}원)")
    else:
      print("❌ 백테스트 실패")

  except KeyboardInterrupt:
    print(f"\n⏹️ 사용자에 의해 백테스트가 중단되었습니다.")
  except Exception as e:
    print(f"❌ 백테스트 중 오류 발생: {e}")
    print(f"\n🔄 기본 백테스트를 실행합니다...")
    print(f"📊 사용자가 선택한 {max_cryptos}개 코인으로 기본 분석을 진행합니다.")

    try:
      results_df = backtest.run_multi_crypto_backtest(days, max_cryptos)
      if not results_df.empty:
        print(f"\n📊 기본 백테스트 결과 (상위 5개):")
        print(results_df.head().to_string(index=False))
        backtest.save_results_to_csv(results_df)

        total_cryptos = len(results_df)
        profitable_cryptos = len(results_df[results_df['Total_Return(%)'] > 0])
        avg_return = results_df['Total_Return(%)'].mean()

        print(f"\n📈 간단 요약:")
        print(f"   성공 코인: {total_cryptos}개")
        print(
          f"   수익 코인: {profitable_cryptos}개 ({profitable_cryptos / total_cryptos * 100:.1f}%)")
        print(f"   평균 수익률: {avg_return:.2f}%")

      else:
        print("❌ 기본 백테스트 결과도 없습니다.")

    except Exception as fallback_error:
      print(f"❌ 기본 백테스트도 실패했습니다: {fallback_error}")
      print(f"\n🔄 최소 설정(5개 코인)으로 재시도합니다...")
      try:
        results_df = backtest.run_multi_crypto_backtest(days, 5)
        if not results_df.empty:
          print(f"✅ 최소 설정 백테스트 성공!")
          print(results_df.head().to_string(index=False))
          backtest.save_results_to_csv(results_df)
        else:
          print("❌ 모든 백테스트 시도가 실패했습니다.")
      except Exception as final_error:
        print(f"❌ 최소 설정 백테스트도 실패: {final_error}")
        print(f"💡 네트워크 연결이나 업비트 API 상태를 확인해주세요.")
        print(f"📦 pyupbit 라이브러리가 설치되어 있는지 확인해주세요: pip install pyupbit")


# ===================================================================================
# 실시간 모니터링 실행
# ===================================================================================

def run_monitor():
  """실시간 모니터링 실행 (대화형)"""
  print("=" * 80)
  print("📡 업비트 코인 실시간 자동 모니터링")
  print("=" * 80)

  telegram_bot_token = os.getenv('UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN')
  telegram_chat_id = os.getenv('UPBIT_BOLLINGER_TELEGRAM_CHAT_ID')

  if not telegram_bot_token or not telegram_chat_id:
    print("⚠️ 텔레그램 설정이 필요합니다!")
    print("💡 설정 방법:")
    print("   1. @BotFather에서 봇 생성 후 토큰 획득")
    print("   2. @userinfobot에서 chat_id 확인")
    print("   3. 환경변수 설정:")
    print("      export UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN='your_bot_token'")
    print("      export UPBIT_BOLLINGER_TELEGRAM_CHAT_ID='your_chat_id'")
    print("\n❌ 텔레그램 설정 없이는 모니터링을 실행할 수 없습니다.")
    return
  else:
    print("✅ 텔레그램 설정 확인됨")

  print(f"\n⚙️ 모니터링 설정:")
  print("1. 5분 간격 (기본값)")
  print("2. 10분 간격")
  print("3. 15분 간격")
  print("4. 30분 간격")
  print("5. 사용자 정의")

  interval_options = {"1": 300, "2": 600, "3": 900, "4": 1800}

  try:
    choice = input("\n스캔 간격 선택 (1-5, 기본값: 1): ").strip() or "1"

    if choice == "5":
      custom_minutes = int(input("사용자 정의 간격 (분): "))
      scan_interval = custom_minutes * 60
    else:
      scan_interval = interval_options.get(choice, 300)

    print(f"✅ 스캔 간격: {scan_interval}초 ({scan_interval // 60}분)")

  except ValueError:
    print("잘못된 입력입니다. 기본값(5분)으로 설정합니다.")
    scan_interval = 300

  monitor = UpbitRealTimeVolatilityMonitor(
      telegram_bot_token=telegram_bot_token,
      telegram_chat_id=telegram_chat_id
  )

  print(f"\n🎯 모니터링 설정 완료:")
  print(f"   📊 감시 코인: {len(monitor.watchlist)}개 (업비트 원화 마켓)")
  print(f"   ⏰ 스캔 간격: {scan_interval // 60}분")
  print(f"   📱 텔레그램 알림: 활성화")
  print(f"   🟢 24시간 거래: 주말에도 모니터링")
  print(f"   🤖 텔레그램 명령어: /ticker, /status, /start")

  # 텔레그램 연결 테스트
  print(f"\n🤖 텔레그램 봇 연결 테스트 중...")
  if monitor.test_telegram_connection():
    print("✅ 텔레그램 연결 성공")
    print("📱 사용 가능한 명령어:")
    print("   • /ticker BTC - 비트코인 분석")
    print("   • /ticker ETH - 이더리움 분석")
    print("   • /status - 모니터링 상태 확인")
    print("   • /start - 도움말 보기")
  else:
    print("⚠️ 텔레그램 연결 실패 - 로그만 출력")

  print(f"\n" + "=" * 80)
  print("🚀 자동 모니터링을 시작합니다!")
  print("   - 명령어 입력 없이 자동으로 30개 코인을 모니터링합니다")
  print("   - 신호 발생시 텔레그램으로 즉시 알림을 전송합니다")
  print("   - 텔레그램에서 /ticker 명령어로 개별 코인 분석 가능")
  print("   - 5회 스캔마다 상태 요약을 전송합니다")
  print("   - 24시간 거래로 주말에도 모니터링합니다")
  print("   - 종료하려면 Ctrl+C를 누르세요")
  print("=" * 80)

  monitor.run_continuous_monitoring(scan_interval)


# ===================================================================================
# 메인 실행 함수
# ===================================================================================

def main():
  """메인 실행 함수"""
  parser = argparse.ArgumentParser(
      description='🚀 업비트 코인 변동성 폭파 볼린저 밴드 트레이딩 시스템',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
📖 사용 예시:
    python upbit_main.py --mode backtest         # 백테스트만 실행
    python upbit_main.py --mode monitor          # 실시간 모니터링 (대화형)
    python upbit_main.py --mode monitor-default  # 백그라운드 모니터링 (기본값)
    python upbit_main.py --mode both             # 백테스트 후 모니터링 실행 (기본값)
  
📱 텔레그램 설정:
    1. @BotFather에서 봇 생성
    2. 봇 토큰 획득
    3. @userinfobot에서 chat_id 확인
    4. 환경변수 설정:
       export UPBIT_BOLLINGER_TELEGRAM_BOT_TOKEN="your_bot_token"
       export UPBIT_BOLLINGER_TELEGRAM_CHAT_ID="your_chat_id"

🔑 업비트 API 설정 (선택사항, 더 안정적인 데이터 수집):
    1. 업비트 > 마이페이지 > Open API 관리
    2. API 키 생성 (일반조회 권한만 체크)
    3. 환경변수 설정:
       export UPBIT_ACCESS_KEY="your_access_key"
       export UPBIT_SECRET_KEY="your_secret_key"

🎯 전략 개요:
    - 변동성 압축 감지 (밴드폭 < 최근 50일 중 20% 하위)
    - RSI > 70 + 변동성 압축 시 매수
    - 분할 익절: BB 80% 위치에서 50% → 하단에서 나머지

📦 필수 라이브러리:
    pip install pyupbit pandas numpy matplotlib telegram-python-bot

🔄 백그라운드 실행 (우분투):
    nohup python upbit_main.py --mode monitor-default > /dev/null 2>&1 &
    # 또는
    python upbit_main.py --mode monitor-default &
        """
  )

  parser.add_argument(
      '--mode', '-m',
      choices=['backtest', 'monitor', 'monitor-default', 'both'],
      default='both',
      help='실행 모드 (기본값: both)'
  )

  args = parser.parse_args()

  print("🚀" + "=" * 78 + "🚀")
  print("     업비트 코인 변동성 폭파 볼린저 밴드 트레이딩 시스템")
  print("🚀" + "=" * 78 + "🚀")
  print(f"⚙️ 실행 모드: {args.mode.upper()}")
  print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  print(f"🐍 Python 버전: {sys.version.split()[0]}")
  print(f"🟢 24시간 거래: 주말에도 모니터링")
  print(
    f"📬 Telegram Commands: Use /ticker to analyze a crypto (e.g., /ticker BTC)")

  # pyupbit 라이브러리 확인
  try:
    import pyupbit
    print(f"📦 pyupbit 라이브러리: 설치됨")
  except ImportError:
    print(f"❌ pyupbit 라이브러리가 설치되지 않았습니다!")
    print(f"📦 설치 명령어: pip install pyupbit")
    print(f"🔄 설치 후 다시 실행해주세요.")
    sys.exit(1)

  # 업비트 API 키 확인
  access_key = os.getenv('UPBIT_ACCESS_KEY')
  secret_key = os.getenv('UPBIT_SECRET_KEY')

  if access_key and secret_key:
    print(f"🔑 업비트 API: 인증 완료 (안정적인 데이터 수집)")
  else:
    print(f"⚠️ 업비트 API: 미설정 (공개 API 사용, 제한적)")
    print(f"💡 더 안정적인 데이터 수집을 위해 API 키 설정을 권장합니다.")
    print(f"   export UPBIT_ACCESS_KEY='your_access_key'")
    print(f"   export UPBIT_SECRET_KEY='your_secret_key'")

  try:
    if args.mode in ['backtest', 'both']:
      run_backtest()

      if args.mode == 'both':
        print(f"\n" + "=" * 80)
        print("🎯 백테스트가 완료되었습니다!")
        print("📡 실시간 모니터링을 시작하려면 Enter를 누르세요...")
        print("🛑 종료하려면 Ctrl+C를 누르세요.")
        print("=" * 80)
        input()

    if args.mode in ['monitor', 'both']:
      run_monitor()

    elif args.mode == 'monitor-default':
      run_monitor_default()

  except KeyboardInterrupt:
    print(f"\n⏹️ 사용자에 의해 프로그램이 중단되었습니다.")

  except Exception as e:
    print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
    print(f"🔧 문제가 지속되면 GitHub Issues에 보고해주세요.")
    print(f"📦 pyupbit 라이브러리가 설치되어 있는지 확인해주세요: pip install pyupbit")

  finally:
    print(f"\n🏁 프로그램을 종료합니다.")
    print(f"📅 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💖 Happy Trading!")


if __name__ == "__main__":
  main()
