# upbit_backtest_strategy.py
"""
업비트 코인 변동성 폭파 볼린저 밴드 백테스트 전용 모듈

주요 기능:
- 변동성 폭파 볼린저 밴드 전략 백테스트 (업비트 코인용)
- 주요 코인 자동 분석
- 상세한 성과 지표 계산 및 시각화
- CSV 결과 저장 및 차트 생성
"""

import os
import platform
import time
import warnings
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyupbit

warnings.filterwarnings('ignore')


# ===================================================================================
# 한글 폰트 설정
# ===================================================================================

def setup_korean_font():
  """한글 폰트 설정"""
  try:
    import matplotlib.font_manager as fm

    system = platform.system()

    if system == "Windows":
      font_candidates = [
        'C:/Windows/Fonts/malgun.ttf',
        'C:/Windows/Fonts/gulim.ttc',
        'C:/Windows/Fonts/batang.ttc'
      ]
      font_names = ['Malgun Gothic', 'Gulim', 'Batang', 'Arial Unicode MS']

    elif system == "Darwin":  # macOS
      font_candidates = [
        '/Library/Fonts/AppleSDGothicNeo.ttc',
        '/System/Library/Fonts/AppleGothic.ttf',
        '/Library/Fonts/NanumGothic.ttf'
      ]
      font_names = ['Apple SD Gothic Neo', 'AppleGothic', 'NanumGothic',
                    'Arial Unicode MS']

    else:  # Linux
      font_candidates = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
        '/usr/share/fonts/TTF/NanumGothic.ttf'
      ]
      font_names = ['NanumGothic', 'DejaVu Sans', 'Liberation Sans']

    font_found = False
    for font_path in font_candidates:
      if os.path.exists(font_path):
        try:
          fm.fontManager.addfont(font_path)
          prop = fm.FontProperties(fname=font_path)
          plt.rcParams['font.family'] = prop.get_name()
          font_found = True
          print(f"✅ 한글 폰트 설정: {font_path}")
          break
        except Exception as e:
          continue

    if not font_found:
      available_fonts = [f.name for f in fm.fontManager.ttflist]
      for font_name in font_names:
        if font_name in available_fonts:
          try:
            plt.rcParams['font.family'] = font_name
            font_found = True
            print(f"✅ 한글 폰트 설정: {font_name}")
            break
          except Exception as e:
            continue

    if not font_found:
      if system == "Windows":
        plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans',
                                       'Arial']
      elif system == "Darwin":
        plt.rcParams['font.family'] = ['Arial Unicode MS', 'Helvetica',
                                       'DejaVu Sans']
      else:
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Liberation Sans',
                                       'Arial']
      print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")

    plt.rcParams['axes.unicode_minus'] = False
    fm._rebuild()
    return font_found

  except Exception as e:
    print(f"⚠️ 폰트 설정 중 오류: {e}")
    plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    return False


setup_korean_font()


# ===================================================================================
# 메인 백테스트 클래스
# ===================================================================================

class UpbitVolatilityBollingerBacktest:
  """업비트 코인 변동성 폭파 볼린저 밴드 백테스트 클래스"""

  def __init__(self, initial_capital: float = 1000000,
      strategy_mode: str = "conservative"):
    """
    초기화

    Parameters:
    initial_capital: 초기 자금 (원, 기본값: 100만원)
    strategy_mode: 전략 모드 ("conservative", "balanced", "aggressive")
    """

    # 업비트 API 키 설정
    self.access_key = os.getenv('UPBIT_ACCESS_KEY')
    self.secret_key = os.getenv('UPBIT_SECRET_KEY')

    # API 키가 있으면 인증된 업비트 객체 생성
    if self.access_key and self.secret_key:
      self.upbit = pyupbit.Upbit(self.access_key, self.secret_key)
      print("✅ 업비트 API 키 인증 완료 - 안정적인 데이터 수집 가능")
    else:
      self.upbit = None
      print("⚠️ 업비트 API 키 없음 - 공개 API 사용 (제한적)")

    # 업비트 주요 코인 리스트 (원화 마켓)
    self.crypto_list = [
      # 메이저 코인
      'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA', 'KRW-DOT',
      # 대형 알트코인
      'KRW-LINK', 'KRW-BCH', 'KRW-TRX', 'KRW-SOL', 'KRW-DOGE'
      # # 중형 알트코인
      'KRW-AVAX', 'KRW-MATIC', 'KRW-ATOM', 'KRW-ALGO',
      # # 소형 알트코인
      'KRW-VET', 'KRW-THETA', 'KRW-FIL', 'KRW-AAVE', 'KRW-CRV',
      # # 한국 인기 코인
      'KRW-DOGE', 'KRW-SHIB', 'KRW-APT', 'KRW-OP', 'KRW-ARB',
      # # DeFi & 신규 코인
      'KRW-UNI', 'KRW-SUSHI', 'KRW-1INCH', 'KRW-SNX', 'KRW-COMP'
    ]

    self.initial_capital = initial_capital
    self.strategy_mode = strategy_mode
    self._setup_parameters(strategy_mode)
    self._setup_output_directories()

    print(f"💰 초기 자금: {self.initial_capital:,.0f}원")
    print(f"📊 전략 모드: {strategy_mode.upper()}")
    print(f"📋 분석 대상: {len(self.crypto_list)}개 코인")

  def _setup_output_directories(self):
    """출력 디렉토리 설정 및 생성"""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    self.output_base_dir = os.path.join(base_dir, 'upbit_output_files')
    self.results_dir = os.path.join(self.output_base_dir, 'results')
    self.charts_dir = os.path.join(self.output_base_dir, 'charts')
    self.reports_dir = os.path.join(self.output_base_dir, 'reports')

    for directory in [self.output_base_dir, self.results_dir, self.charts_dir,
                      self.reports_dir]:
      try:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 디렉토리 준비: {os.path.relpath(directory)}")
      except Exception as e:
        print(f"⚠️ 디렉토리 생성 오류 ({directory}): {e}")
        if directory == self.results_dir:
          self.results_dir = base_dir
        elif directory == self.charts_dir:
          self.charts_dir = base_dir
        elif directory == self.reports_dir:
          self.reports_dir = base_dir

  def _setup_parameters(self, strategy_mode: str):
    """전략 매개변수 설정"""
    self.bb_period = 20
    self.bb_std_multiplier = 2.0
    self.rsi_period = 14
    self.volatility_lookback = 50
    self.volatility_threshold = 0.2

    if strategy_mode == "aggressive":
      self.rsi_overbought = 60
      self.bb_sell_threshold = 0.7
      self.bb_sell_all_threshold = 0.2
      print("🔥 공격적 전략: 더 많은 매매 기회, 높은 수익 추구")
    elif strategy_mode == "balanced":
      self.rsi_overbought = 65
      self.bb_sell_threshold = 0.75
      self.bb_sell_all_threshold = 0.15
      print("⚖️ 균형 전략: 적당한 위험과 수익")
    else:  # conservative
      self.rsi_overbought = 70
      self.bb_sell_threshold = 0.8
      self.bb_sell_all_threshold = 0.1
      print("🛡️ 보수적 전략: 안전 우선, 신중한 매매")

  def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 계산 (수정된 볼린저 스퀴즈 전략)"""
    if len(data) < max(self.bb_period, self.rsi_period, self.volatility_lookback):
      return data

    # 볼린저 밴드
    data['SMA'] = data['close'].rolling(window=self.bb_period).mean()
    data['STD'] = data['close'].rolling(window=self.bb_period).std()
    data['Upper_Band'] = data['SMA'] + (data['STD'] * self.bb_std_multiplier)
    data['Lower_Band'] = data['SMA'] - (data['STD'] * self.bb_std_multiplier)

    # 밴드폭 (변동성 지표)
    data['Band_Width'] = (data['Upper_Band'] - data['Lower_Band']) / data['SMA']

    # 스퀴즈 감지 (최근 20일 중 최소값과 비교) - 컬럼명 통일
    data['Volatility_Squeeze'] = data['Band_Width'] < data['Band_Width'].rolling(20).min() * 1.1

    # 볼린저 밴드 위치 (0~1)
    data['BB_Position'] = (data['close'] - data['Lower_Band']) / (
        data['Upper_Band'] - data['Lower_Band'])

    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # 가격 모멘텀 (스퀴즈 브레이크아웃 감지)
    data['Price_Change'] = data['close'].pct_change()
    data['Volume_MA'] = data['volume'].rolling(20).mean() if 'volume' in data.columns else 1
    data['Volume_Ratio'] = data['volume'] / data['Volume_MA'] if 'volume' in data.columns else 1

    # 수정된 매매 신호 - 컬럼명 통일
    # 매수: 스퀴즈 상태에서 상단 밴드 돌파 + 거래량 증가
    data['Buy_Signal'] = (
        data['Volatility_Squeeze'] &  # BB_Squeeze → Volatility_Squeeze로 변경
        (data['close'] > data['Upper_Band']) &
        (data['Volume_Ratio'] > 1.2) &  # 거래량 20% 증가
        (data['RSI'] > 50) & (data['RSI'] < 80)  # RSI 중립~과매수 초기
    )

    # 50% 익절: BB 상단 근처
    data['Sell_50_Signal'] = data['BB_Position'] >= 0.85

    # 전량 매도: BB 하단 근처 또는 손절
    data['Sell_All_Signal'] = (data['BB_Position'] <= 0.15) | (data['RSI'] < 30)

    return data

  def get_crypto_data(self, symbol: str, days: int = 1100) -> Optional[
    pd.DataFrame]:
    """업비트에서 코인 데이터 가져오기 (강화된 오류 처리)"""
    max_retries = 3

    for attempt in range(max_retries):
      try:
        if attempt > 0:
          time.sleep(1)  # 재시도 전 대기

        data = None

        # 방법 1: API 키가 있으면 인증된 API 시도
        if self.upbit and attempt < 2:
          try:
            data = pyupbit.get_ohlcv(symbol, interval="day", count=days,
                                     to=None)
          except Exception as e:
            if "Length mismatch" in str(e):
              pass

        # 방법 2: 공개 API 시도 (더 작은 데이터 요청)
        if data is None or data.empty:
          try:
            # 더 작은 단위로 요청
            count = min(days, 200) if attempt == 0 else min(days, 100)
            data = pyupbit.get_ohlcv(symbol, interval="day", count=count)
          except Exception as e:
            if "Length mismatch" in str(e):
              continue

        # 방법 3: 최소 데이터로 재시도
        if (data is None or data.empty) and attempt == max_retries - 1:
          try:
            data = pyupbit.get_ohlcv(symbol, interval="day", count=50)
          except:
            pass

        if data is None or data.empty:
          if attempt == max_retries - 1:
            return None
          continue

        # 데이터 전처리 및 검증
        try:
          # 1. 인덱스를 datetime으로 변환
          if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

          # 2. 컬럼 정리
          if len(data.columns) >= 5:
            # 첫 5개 컬럼만 사용
            data = data.iloc[:, :5].copy()
            data.columns = ['open', 'high', 'low', 'close', 'volume']
          else:
            # 컬럼명 매핑
            col_mapping = {}
            for i, col in enumerate(data.columns):
              if i == 0 or 'open' in str(col).lower():
                col_mapping[col] = 'open'
              elif i == 1 or 'high' in str(col).lower():
                col_mapping[col] = 'high'
              elif i == 2 or 'low' in str(col).lower():
                col_mapping[col] = 'low'
              elif i == 3 or 'close' in str(col).lower():
                col_mapping[col] = 'close'
              elif i == 4 or 'volume' in str(col).lower():
                col_mapping[col] = 'volume'
            data = data.rename(columns=col_mapping)

          # 3. 필수 컬럼 확인
          required_cols = ['open', 'high', 'low', 'close', 'volume']
          missing_cols = [col for col in required_cols if
                          col not in data.columns]
          if missing_cols:
            if attempt == max_retries - 1:
              return None
            continue

          # 4. 데이터 길이 불일치 해결
          lengths = [len(data[col].dropna()) for col in required_cols]
          min_length = min(lengths)
          max_length = max(lengths)

          if max_length > min_length:
            # 모든 컬럼을 최소 길이로 맞춤
            data = data.iloc[:min_length].copy()

          # 5. NaN 값 처리
          data = data.dropna()
          if len(data) < self.volatility_lookback:
            if attempt == max_retries - 1:
              return None
            continue

          # 6. 데이터 타입 변환
          for col in required_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')

          # 7. 최종 검증
          if data['close'].isna().sum() > len(data) * 0.1:
            if attempt == max_retries - 1:
              return None
            continue

          # 8. 가격 검증
          avg_price = data['close'].mean()
          if avg_price < 1:
            if attempt == max_retries - 1:
              return None
            continue

          return data

        except Exception as e:
          if attempt == max_retries - 1:
            return None
          continue

      except Exception as e:
        if attempt == max_retries - 1:
          return None
        continue

    return None

  def run_single_backtest(self, symbol: str, days: int = 1100) -> Optional[
    Dict]:
    """단일 코인 백테스트"""
    try:
      # 데이터 다운로드
      data = self.get_crypto_data(symbol, days)
      if data is None:
        return None

      # 기술적 지표 계산
      data = self.calculate_technical_indicators(data)

      # 지표 검증
      if data['RSI'].isna().all() or data['SMA'].isna().all():
        return None

      # 백테스트 실행
      result = self._execute_backtest(data, symbol)
      result['data'] = data

      return result

    except Exception as e:
      return None

  def _execute_backtest(self, data: pd.DataFrame, symbol: str) -> Dict:
    """백테스트 로직 실행"""
    position = 0  # 0: 노포지션, 1: 50%, 2: 100%
    cash = self.initial_capital
    coins = 0
    trades = []
    equity_curve = []

    for i in range(len(data)):
      current_price = data.iloc[i]['close']
      current_date = data.index[i]

      # 매수 신호
      if data.iloc[i]['Buy_Signal'] and position == 0:
        coins = cash / current_price
        position = 2

        trades.append({
          'date': current_date,
          'action': 'BUY',
          'price': current_price,
          'coins': coins,
          'value': cash
        })
        cash = 0  # 전액 투자

      # 50% 익절
      elif data.iloc[i]['Sell_50_Signal'] and position == 2:
        sell_coins = coins * 0.5
        sell_value = sell_coins * current_price
        cash += sell_value
        coins -= sell_coins
        position = 1

        trades.append({
          'date': current_date,
          'action': 'SELL_50%',
          'price': current_price,
          'coins': sell_coins,
          'value': sell_value
        })

      # 전량 매도
      elif data.iloc[i]['Sell_All_Signal'] and position > 0:
        sell_value = coins * current_price
        cash += sell_value

        trades.append({
          'date': current_date,
          'action': 'SELL_ALL',
          'price': current_price,
          'coins': coins,
          'value': sell_value
        })

        coins = 0
        position = 0

      # 자산가치 기록
      portfolio_value = cash + (coins * current_price)
      equity_curve.append({
        'date': current_date,
        'portfolio_value': portfolio_value,
        'cash': cash,
        'crypto_value': coins * current_price
      })

    # 마지막 포지션 청산
    if coins > 0:
      cash += coins * data.iloc[-1]['close']

    # 성과 지표 계산
    metrics = self._calculate_metrics(trades, equity_curve, cash, len(data))

    return {
      'symbol': symbol,
      'trades': trades,
      'equity_curve': equity_curve,
      'final_cash': cash,
      **metrics
    }

  def _calculate_metrics(self, trades: List[Dict], equity_curve: List[Dict],
      final_cash: float, test_days: int) -> Dict:
    """성과 지표 계산"""
    total_return = (
                         final_cash - self.initial_capital) / self.initial_capital * 100

    # 거래 분석
    completed_trades = self._analyze_trades(trades)

    # 통계 계산
    total_trades = len(completed_trades)
    winning_trades = sum(1 for t in completed_trades if t['is_winning'])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # 수익/손실 분석
    profits = [t['profit_pct'] for t in completed_trades if t['is_winning']]
    losses = [t['profit_pct'] for t in completed_trades if not t['is_winning']]

    avg_profit = np.mean(profits) if profits else 0
    avg_loss = np.mean(losses) if losses else 0
    profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else float(
      'inf')

    # 최대 낙폭
    max_drawdown = self._calculate_max_drawdown(equity_curve)

    return {
      'total_return': total_return,
      'win_rate': win_rate,
      'total_trades': total_trades,
      'winning_trades': winning_trades,
      'avg_profit': avg_profit,
      'avg_loss': avg_loss,
      'profit_factor': profit_factor,
      'max_drawdown': max_drawdown,
      'final_value': final_cash,
      'completed_trades': completed_trades,
      'test_period_days': test_days
    }

  def _analyze_trades(self, trades: List[Dict]) -> List[Dict]:
    """거래 분석"""
    completed_trades = []
    buy_trade = None

    for trade in trades:
      if trade['action'] == 'BUY':
        buy_trade = trade
      elif buy_trade and trade['action'] in ['SELL_50%', 'SELL_ALL']:
        profit_pct = (trade['price'] - buy_trade['price']) / buy_trade[
          'price'] * 100

        completed_trades.append({
          'entry_date': buy_trade['date'],
          'exit_date': trade['date'],
          'entry_price': buy_trade['price'],
          'exit_price': trade['price'],
          'profit_pct': profit_pct,
          'is_winning': profit_pct > 0
        })

        if trade['action'] == 'SELL_ALL':
          buy_trade = None

    return completed_trades

  def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
    """최대 낙폭 계산"""
    if not equity_curve:
      return 0

    portfolio_values = [eq['portfolio_value'] for eq in equity_curve]
    peak = portfolio_values[0]
    max_drawdown = 0

    for value in portfolio_values:
      if value > peak:
        peak = value
      drawdown = (peak - value) / peak * 100
      if drawdown > max_drawdown:
        max_drawdown = drawdown

    return max_drawdown

  def run_multi_crypto_backtest(self, days: int = 1095,
      max_cryptos: int = 20) -> pd.DataFrame:
    """다중 코인 백테스트"""
    results = []
    cryptos_to_test = self.crypto_list[:max_cryptos]
    failed_cryptos = []

    print(f"🔍 {len(cryptos_to_test)}개 코인 백테스트 시작...")
    print(f"📅 기간: 최근 {days}일 (약 {days // 365}년)")
    print(f"⚠️  중단하려면 Ctrl+C를 누르세요")
    print("-" * 80)

    try:
      for i, symbol in enumerate(cryptos_to_test):
        print(f"진행: {i + 1:2d}/{len(cryptos_to_test)} - {symbol:10s} ... ",
              end="")

        retry_count = 0
        max_retries = 3
        success = False

        while retry_count < max_retries and not success:
          try:
            result = self.run_single_backtest(symbol, days)
            if result:
              results.append(result)
              print(f"완료 (수익률: {result['total_return']:6.2f}%)")
              success = True
            else:
              if retry_count < max_retries - 1:
                print(f"데이터 부족 - 재시도 {retry_count + 1}/{max_retries}", end="")
                time.sleep(1)
              retry_count += 1

          except KeyboardInterrupt:
            print(f"\n⏹️  백테스트가 중단되었습니다.")
            raise
          except Exception as e:
            if retry_count < max_retries - 1:
              print(f"오류 - 재시도 {retry_count + 1}/{max_retries}", end="")
              time.sleep(1)
            retry_count += 1

        if not success:
          failed_cryptos.append(symbol)
          print(" - 최종 실패")

        if i < len(cryptos_to_test) - 1:
          time.sleep(0.1)

        if (i + 1) % 10 == 0:
          success_count = len(results)
          print(
            f"\n📊 중간 요약: {success_count}/{i + 1} 성공 ({success_count / (i + 1) * 100:.1f}%)")
          print("-" * 80)

    except KeyboardInterrupt:
      print(f"\n⏹️  다중 코인 백테스트가 중단되었습니다.")

    # 최종 결과 요약
    print(f"\n" + "=" * 80)
    print(f"📊 백테스트 완료 요약")
    print(f"=" * 80)
    print(f"✅ 성공: {len(results)}개 코인")
    print(f"❌ 실패: {len(failed_cryptos)}개 코인")
    print(f"📈 성공률: {len(results) / len(cryptos_to_test) * 100:.1f}%")

    if failed_cryptos:
      print(f"\n❌ 실패한 코인들:")
      for i, symbol in enumerate(failed_cryptos):
        print(f"   {i + 1}. {symbol}")

    if not results:
      print("\n❌ 분석 가능한 코인이 없습니다.")
      return pd.DataFrame()

    # DataFrame 변환
    df_results = pd.DataFrame([
      {
        'Symbol': r['symbol'],
        'Initial_Capital(₩)': f"{self.initial_capital:,.0f}원",
        'Final_Value(₩)': f"{r['final_value']:,.0f}원",
        'Profit(₩)': f"{r['final_value'] - self.initial_capital:,.0f}원",
        'Total_Return(%)': round(r['total_return'], 2),
        'Win_Rate(%)': round(r['win_rate'], 2),
        'Total_Trades': r['total_trades'],
        'Winning_Trades': r['winning_trades'],
        'Avg_Profit(%)': round(r['avg_profit'], 2),
        'Avg_Loss(%)': round(r['avg_loss'], 2),
        'Profit_Factor': round(r['profit_factor'], 2),
        'Max_Drawdown(%)': round(r['max_drawdown'], 2),
        'Test_Days': r.get('test_period_days', 0)
      }
      for r in results
    ])

    return df_results.sort_values('Total_Return(%)', ascending=False)

  def run_comprehensive_analysis(self, days: int = 1095, max_cryptos: int = 20,
      detailed_analysis: str = "top5", save_charts: bool = True) -> Dict:
    """종합 분석 실행"""
    print("=" * 80)
    print("🚀 업비트 코인 변동성 폭파 볼린저 밴드 종합 분석")
    print("=" * 80)

    # 1. 다중 코인 백테스트
    results_df = self.run_multi_crypto_backtest(days, max_cryptos)

    if results_df.empty:
      return {}

    # 2. 요약 통계 출력
    self._print_summary_statistics(results_df)

    # 3. 리스크 분석
    self._print_risk_analysis(results_df)

    # 4. 결과 저장
    self.save_results_to_csv(results_df)

    # 5. 투자 리포트 생성
    self._save_investment_report(results_df, days)

    # 6. 상세 분석
    detailed_results = []
    if detailed_analysis != "none":
      symbols_to_analyze = self._select_analysis_symbols(results_df,
                                                         detailed_analysis)
      if symbols_to_analyze:
        print(f"\n📊 상세 분석 시작: {len(symbols_to_analyze)}개 코인")
        detailed_results = self._run_detailed_analysis(symbols_to_analyze, days,
                                                       save_charts)

    return {
      'summary_results': results_df,
      'detailed_results': detailed_results,
      'statistics': self._calculate_summary_stats(results_df)
    }

  def _select_analysis_symbols(self, results_df: pd.DataFrame, mode: str) -> \
  List[str]:
    """분석할 코인 선택"""
    if mode == "top3":
      return results_df.head(3)['Symbol'].tolist()
    elif mode == "top5":
      return results_df.head(5)['Symbol'].tolist()
    elif mode == "positive":
      return results_df[results_df['Total_Return(%)'] > 0]['Symbol'].tolist()
    elif mode == "all":
      return results_df['Symbol'].tolist()
    else:
      return []

  def _run_detailed_analysis(self, symbols: List[str], days: int,
      save_charts: bool = True) -> List[Dict]:
    """상세 분석 실행"""
    detailed_results = []

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if save_charts:
      print(f"📁 차트 저장 디렉토리: {os.path.relpath(self.charts_dir)}/")

    for i, symbol in enumerate(symbols):
      print(f"\n📈 상세 분석 {i + 1}/{len(symbols)}: {symbol}")
      print("-" * 50)

      try:
        result = self.run_single_backtest(symbol, days)
        if result:
          if save_charts:
            filename = f"{symbol.replace('KRW-', '')}_analysis_{timestamp}.png"
            self._create_analysis_chart(result, save_path=filename)
          else:
            self._create_analysis_chart(result, show_chart=True)

          self._print_detailed_results(result)
          detailed_results.append(result)
        else:
          print(f"❌ {symbol} 분석 실패")

      except Exception as e:
        print(f"❌ {symbol} 분석 중 오류: {e}")

    if save_charts and detailed_results:
      print(
        f"\n📊 총 {len(detailed_results)}개 차트가 {os.path.relpath(self.charts_dir)}/ 디렉토리에 저장되었습니다.")

    return detailed_results

  def _create_analysis_chart(self, result: Dict, save_path: str = None,
      show_chart: bool = False):
    """분석 차트 생성"""
    data = result['data']
    trades = result['trades']
    equity_curve = result['equity_curve']
    symbol = result['symbol']

    fig, axes = plt.subplots(4, 1, figsize=(15, 12))
    fig.suptitle(f'{symbol} - 변동성 폭파 볼린저 밴드 전략 분석', fontsize=16,
                 fontweight='bold')

    # 1. 가격 & 볼린저 밴드
    ax1 = axes[0]
    ax1.plot(data.index, data['close'], 'k-', linewidth=1.5, label='종가')
    ax1.plot(data.index, data['Upper_Band'], 'r--', alpha=0.7, label='상단밴드')
    ax1.plot(data.index, data['SMA'], 'b-', alpha=0.7, label='중간밴드')
    ax1.plot(data.index, data['Lower_Band'], 'g--', alpha=0.7, label='하단밴드')
    ax1.fill_between(data.index, data['Upper_Band'], data['Lower_Band'],
                     alpha=0.1, color='gray')

    # 매매 신호 표시
    buy_signals = [t for t in trades if t['action'] == 'BUY']
    sell_50_signals = [t for t in trades if t['action'] == 'SELL_50%']
    sell_all_signals = [t for t in trades if t['action'] == 'SELL_ALL']

    if buy_signals:
      dates = [t['date'] for t in buy_signals]
      prices = [t['price'] for t in buy_signals]
      ax1.scatter(dates, prices, color='green', marker='^', s=100, zorder=5,
                  label='매수')

    if sell_50_signals:
      dates = [t['date'] for t in sell_50_signals]
      prices = [t['price'] for t in sell_50_signals]
      ax1.scatter(dates, prices, color='orange', marker='v', s=100, zorder=5,
                  label='50% 매도')

    if sell_all_signals:
      dates = [t['date'] for t in sell_all_signals]
      prices = [t['price'] for t in sell_all_signals]
      ax1.scatter(dates, prices, color='red', marker='v', s=100, zorder=5,
                  label='전량매도')

    ax1.set_title('가격 & 볼린저밴드 & 매매신호', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. RSI
    ax2 = axes[1]
    ax2.plot(data.index, data['RSI'], 'purple', linewidth=1.5, label='RSI')
    ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='과매수 (70)')
    ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='과매도 (30)')
    ax2.fill_between(data.index, 70, 100, alpha=0.2, color='red')
    ax2.fill_between(data.index, 0, 30, alpha=0.2, color='green')
    ax2.set_title('RSI (상대강도지수)', fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. 변동성 지표
    # 3. 변동성 지표 부분에서
    ax3 = axes[2]
    ax3.plot(data.index, data['Band_Width'], 'brown', linewidth=1.5, label='밴드폭')
    squeeze_data = data[data['Volatility_Squeeze']]  # BB_Squeeze → Volatility_Squeeze로 변경
    if not squeeze_data.empty:
      ax3.scatter(squeeze_data.index, squeeze_data['Band_Width'], color='red',
                  s=20, alpha=0.7, label='변동성 압축')
    ax3.set_title('변동성 지표 (밴드폭 & 압축구간)', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. 자산 곡선
    ax4 = axes[3]
    if equity_curve:
      dates = [eq['date'] for eq in equity_curve]
      values = [eq['portfolio_value'] for eq in equity_curve]
      ax4.plot(dates, values, 'darkgreen', linewidth=2, label='포트폴리오 가치')
      ax4.axhline(y=self.initial_capital, color='gray', linestyle='--',
                  alpha=0.7, label='초기자본')

      final_return = ((values[
                         -1] - self.initial_capital) / self.initial_capital) * 100
      final_profit = values[-1] - self.initial_capital

      info_text = f'총 수익률: {final_return:.2f}%\n총 수익금: {final_profit:,.0f}원'
      ax4.text(0.02, 0.85, info_text, transform=ax4.transAxes, fontsize=11,
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    ax4.set_title('포트폴리오 자산 곡선', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # X축 레이블 회전
    for ax in axes:
      ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()

    # 저장 또는 출력
    if save_path:
      try:
        if not os.path.isabs(save_path):
          save_path = os.path.join(self.charts_dir, save_path)

        chart_dir = os.path.dirname(save_path)
        os.makedirs(chart_dir, exist_ok=True)

        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"📊 차트 저장: {os.path.relpath(save_path)}")
      except Exception as e:
        print(f"❌ 차트 저장 실패: {e}")
        try:
          filename = os.path.basename(save_path)
          fallback_path = os.path.join(self.charts_dir, filename)
          plt.savefig(fallback_path, dpi=200, bbox_inches='tight')
          plt.close()
          print(f"📊 차트 저장 (대안 경로): {os.path.relpath(fallback_path)}")
        except Exception as e2:
          print(f"❌ 대안 차트 저장도 실패: {e2}")
          plt.close()
    elif show_chart:
      plt.show()
    else:
      plt.close()

  def _print_summary_statistics(self, results_df: pd.DataFrame):
    """요약 통계 출력"""
    print(f"\n📊 백테스트 결과 요약:")
    print("-" * 140)
    print(results_df.to_string(index=False))

    print(f"\n📈 전체 통계:")
    print("-" * 70)

    total_cryptos = len(results_df)
    profitable_cryptos = len(results_df[results_df['Total_Return(%)'] > 0])
    avg_return = results_df['Total_Return(%)'].mean()
    avg_win_rate = results_df['Win_Rate(%)'].mean()
    avg_drawdown = results_df['Max_Drawdown(%)'].mean()

    # 수익금 통계
    profits = []
    for profit_str in results_df['Profit(₩)']:
      profit_val = float(profit_str.replace('원', '').replace(',', ''))
      profits.append(profit_val)

    avg_profit = np.mean(profits) if profits else 0

    best = results_df.iloc[0]
    worst = results_df.iloc[-1]

    print(f"💰 초기 자금:     {self.initial_capital:>10,.0f}원")
    print(f"📊 분석 코인 수:   {total_cryptos:>10d}개")
    print(
      f"✅ 수익 코인 수:   {profitable_cryptos:>10d}개 ({profitable_cryptos / total_cryptos * 100:.1f}%)")
    print(f"📈 평균 수익률:   {avg_return:>10.2f}%")
    print(f"💲 평균 수익금:   {avg_profit:>10,.0f}원")
    print(f"🎯 평균 승률:     {avg_win_rate:>10.2f}%")
    print(f"📉 평균 최대낙폭: {avg_drawdown:>10.2f}%")
    print(f"🏆 최고 수익:     {best['Symbol']} ({best['Total_Return(%)']:6.2f}%)")
    print(f"📉 최저 수익:     {worst['Symbol']} ({worst['Total_Return(%)']:6.2f}%)")

    # 포트폴리오 시뮬레이션
    portfolio_return = avg_return
    portfolio_profit = (portfolio_return / 100) * self.initial_capital

    print(f"\n💼 포트폴리오 시뮬레이션 (동일 비중 투자):")
    print(f"   예상 수익률:    {portfolio_return:>10.2f}%")
    print(f"   예상 수익금:    {portfolio_profit:>10,.0f}원")
    print(f"   예상 최종자산:  {self.initial_capital + portfolio_profit:>10,.0f}원")

  def _print_detailed_results(self, result: Dict):
    """상세 결과 출력"""
    symbol = result['symbol']
    final_value = result['final_value']
    total_profit = final_value - self.initial_capital

    print(f"\n{'=' * 70}")
    print(f"📊 {symbol} 백테스트 상세 결과")
    print(f"{'=' * 70}")
    print(f"💰 초기 자금:      {self.initial_capital:>10,.0f}원")
    print(f"💵 최종 자산:      {final_value:>10,.0f}원")
    print(f"💲 총 수익금:      {total_profit:>10,.0f}원")
    print(f"📈 총 수익률:      {result['total_return']:>10.2f}%")
    print(f"🎯 승률:          {result['win_rate']:>10.2f}%")
    print(f"🔢 총 거래 횟수:   {result['total_trades']:>10d}회")
    print(f"✅ 수익 거래:      {result['winning_trades']:>10d}회")
    print(f"📊 평균 수익:      {result['avg_profit']:>10.2f}%")
    print(f"📉 평균 손실:      {result['avg_loss']:>10.2f}%")
    print(f"⚖️ 손익비:        {result['profit_factor']:>10.2f}")
    print(f"📉 최대 낙폭:      {result['max_drawdown']:>10.2f}%")

    # 연율화 수익률
    if result.get('test_period_days', 0) > 0:
      test_days = result['test_period_days']
      annualized_return = ((final_value / self.initial_capital) ** (
            365 / test_days) - 1) * 100
      print(f"📅 테스트 기간:    {test_days:>10d}일")
      print(f"📊 연율화 수익률:  {annualized_return:>10.2f}%")

    # 성과 평가
    if result['total_return'] > 20:
      evaluation = "🌟 우수"
    elif result['total_return'] > 10:
      evaluation = "✅ 양호"
    elif result['total_return'] > 0:
      evaluation = "📈 수익"
    else:
      evaluation = "📉 손실"
    print(f"🏆 성과 평가:      {evaluation:>10s}")

    print(f"{'=' * 70}")

  def _print_risk_analysis(self, results_df: pd.DataFrame):
    """리스크 분석 결과 출력"""
    if results_df.empty:
      return

    returns = results_df['Total_Return(%)'].values

    # 기본 통계
    mean_return = np.mean(returns)
    std_return = np.std(returns)

    # 리스크 지표
    sharpe_ratio = mean_return / std_return if std_return > 0 else 0
    var_95 = np.percentile(returns, 5)
    max_loss = np.min(returns)
    success_rate = len(returns[returns > 0]) / len(returns) * 100

    # 리스크 등급
    if std_return <= 10:
      risk_grade = "🟢 낮음"
    elif std_return <= 20:
      risk_grade = "🟡 보통"
    else:
      risk_grade = "🔴 높음"

    print(f"\n📊 리스크 분석:")
    print("-" * 50)
    print(f"📈 평균 수익률:    {mean_return:8.2f}%")
    print(f"📊 변동성:        {std_return:8.2f}%")
    print(f"⚖️ 샤프 비율:     {sharpe_ratio:8.2f}")
    print(f"⚠️ 95% VaR:      {var_95:8.2f}%")
    print(f"💥 최대 손실:     {max_loss:8.2f}%")
    print(f"🎯 성공 확률:     {success_rate:8.1f}%")
    print(f"🚦 리스크 등급:   {risk_grade}")

  def _save_investment_report(self, results_df: pd.DataFrame, days: int):
    """투자 리포트 저장"""
    if results_df.empty:
      return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'upbit_investment_report_{timestamp}.txt'

    # 기본 통계 계산
    total_cryptos = len(results_df)
    profitable_cryptos = len(results_df[results_df['Total_Return(%)'] > 0])
    avg_return = results_df['Total_Return(%)'].mean()

    # 성과 분석
    excellent_cryptos = len(results_df[results_df['Total_Return(%)'] >= 20])
    good_cryptos = len(results_df[(results_df['Total_Return(%)'] >= 10) &
                                  (results_df['Total_Return(%)'] < 20)])

    # 포트폴리오 추천
    top_3 = results_df.head(3)

    # 리포트 작성
    report = f"""📊 업비트 코인 투자 분석 리포트
{'=' * 60}
📅 분석 기간: 최근 {days}일 (약 {days // 365}년)
💰 초기 자금: {self.initial_capital:,.0f}원
⚙️ 전략 모드: {self.strategy_mode.upper()}

📈 성과 요약:
   • 분석 코인: {total_cryptos}개
   • 수익 코인: {profitable_cryptos}개 ({profitable_cryptos / total_cryptos * 100:.1f}%)
   • 평균 수익률: {avg_return:.2f}%
   
🏆 성과 등급별 분포:
   • 우수 (20%+): {excellent_cryptos}개
   • 양호 (10-20%): {good_cryptos}개
   • 수익 (0-10%): {profitable_cryptos - excellent_cryptos - good_cryptos}개

🎯 투자 추천:
"""

    # 공격적 포트폴리오
    if not top_3.empty:
      report += "\n   📈 공격적 포트폴리오 (수익률 우선):\n"
      for i, (_, row) in enumerate(top_3.iterrows()):
        profit_amount = (row['Total_Return(%)'] / 100) * self.initial_capital
        report += f"      {i + 1}. {row['Symbol']}: {row['Total_Return(%)']}% ({profit_amount:,.0f}원)\n"

    # 투자 전략 추천
    if avg_return > 15:
      strategy_advice = "💪 강세장 전략: 적극적 투자 추천"
    elif avg_return > 5:
      strategy_advice = "⚖️ 균형 전략: 분산 투자 추천"
    else:
      strategy_advice = "🛡️ 보수적 전략: 신중한 투자 필요"

    report += f"\n💡 추천 투자 전략: {strategy_advice}\n"

    # 주의사항
    report += f"""
⚠️ 투자 주의사항:
   • 과거 성과는 미래 수익을 보장하지 않습니다
   • 분산 투자를 통해 리스크를 관리하세요
   • 손실 허용 범위 내에서 투자하세요
   • 코인은 주식보다 변동성이 매우 높습니다

📊 사용된 전략 파라미터:
   • 볼린저 밴드: {self.bb_period}일, {self.bb_std_multiplier}σ
   • RSI 임계값: {self.rsi_overbought}
   • 변동성 압축: 하위 {self.volatility_threshold * 100}%

{'=' * 60}
리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 파일 저장
    output_path = os.path.join(self.reports_dir, filename)

    try:
      with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
      print(f"📋 투자 리포트 저장: {os.path.relpath(output_path)}")
      return filename
    except Exception as e:
      print(f"❌ 리포트 저장 실패: {e}")
      return None

  def _calculate_summary_stats(self, results_df: pd.DataFrame) -> Dict:
    """요약 통계 계산"""
    return {
      'total_cryptos': len(results_df),
      'profitable_cryptos': len(results_df[results_df['Total_Return(%)'] > 0]),
      'average_return': results_df['Total_Return(%)'].mean(),
      'median_return': results_df['Total_Return(%)'].median(),
      'best_crypto': results_df.iloc[0]['Symbol'],
      'best_return': results_df.iloc[0]['Total_Return(%)'],
      'worst_crypto': results_df.iloc[-1]['Symbol'],
      'worst_return': results_df.iloc[-1]['Total_Return(%)']
    }

  def save_results_to_csv(self, results_df: pd.DataFrame, filename: str = None):
    """결과를 CSV로 저장"""
    if results_df.empty:
      print("❌ 저장할 결과가 없습니다.")
      return None

    if filename is None:
      timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
      filename = f'upbit_backtest_results_{timestamp}.csv'

    output_path = os.path.join(self.results_dir, filename)

    try:
      results_df.to_csv(output_path, index=False, encoding='utf-8')
      print(f"💾 백테스트 결과 저장: {os.path.relpath(output_path)}")
      return filename
    except Exception as e:
      print(f"❌ 백테스트 결과 저장 실패: {e}")
      return None


# ===================================================================================
# 메인 실행 함수
# ===================================================================================

def main():
  """메인 실행 함수"""
  print("🚀 업비트 코인 변동성 폭파 볼린저 밴드 백테스트")
  print("=" * 50)

  # 초기 자금 설정
  print("💰 초기 자금 설정:")
  try:
    capital = float(input("초기 자금을 입력하세요 (원): "))
    backtest = UpbitVolatilityBollingerBacktest(initial_capital=capital)
  except ValueError:
    print("잘못된 입력입니다. 기본값 1,000,000원을 사용합니다.")
    backtest = UpbitVolatilityBollingerBacktest(initial_capital=1000000)

  # 백테스트 기간 설정
  days = 1095  # 3년
  print(f"📅 분석 기간: 최근 {days}일 (약 3년)")

  # 종합 분석 실행
  results = backtest.run_comprehensive_analysis(
      days=days,
      max_cryptos=15,
      detailed_analysis="top3",
      save_charts=True
  )

  if results:
    print(f"\n✅ 분석 완료!")

    # 투자 권장사항
    summary_results = results.get('summary_results')
    if not summary_results.empty:
      top_performers = summary_results.head(3)
      print(f"\n🏆 투자 추천 코인 (상위 3개):")
      for i, (_, row) in enumerate(top_performers.iterrows()):
        print(f"{i + 1}. {row['Symbol']}: {row['Total_Return(%)']}% 수익률")

  else:
    print(f"\n❌ 분석 실패")


if __name__ == "__main__":
  main()
