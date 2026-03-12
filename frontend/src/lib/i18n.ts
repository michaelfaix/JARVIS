// =============================================================================
// src/lib/i18n.ts — Lightweight i18n system (no external libraries)
// =============================================================================

export type Locale = 'en' | 'de';

export type TranslationKey =
  // Navigation
  | 'nav_dashboard'
  | 'nav_charts'
  | 'nav_signals'
  | 'nav_portfolio'
  | 'nav_risk_guardian'
  | 'nav_opportunity_radar'
  | 'nav_strategy_lab'
  | 'nav_ai_chat'
  | 'nav_markets'
  | 'nav_trade_journal'
  | 'nav_price_alerts'
  | 'nav_leaderboard'
  | 'nav_settings'
  | 'nav_social_trading'
  | 'nav_sign_out'
  // Dashboard
  | 'dashboard_market_overview'
  | 'dashboard_total_value'
  | 'dashboard_total_pnl'
  | 'dashboard_open_positions'
  | 'dashboard_drawdown'
  | 'dashboard_win_rate'
  | 'dashboard_top_signals'
  | 'dashboard_portfolio_summary'
  | 'dashboard_market_pulse'
  | 'dashboard_fear_greed'
  // Signals
  | 'signals_active'
  | 'signals_long'
  | 'signals_short'
  | 'signals_avg_confidence'
  | 'signals_direction'
  | 'signals_entry'
  | 'signals_stop_loss'
  | 'signals_take_profit'
  | 'signals_confidence'
  | 'signals_quality'
  | 'signals_action'
  | 'signals_accept'
  | 'signals_close'
  | 'signals_trade'
  | 'signals_pending_orders'
  // Portfolio
  | 'portfolio_paper_trading_account'
  | 'portfolio_asset_allocation'
  | 'portfolio_available_capital'
  | 'portfolio_risk_score'
  | 'portfolio_position_size'
  | 'portfolio_auto_sl_tp'
  | 'portfolio_trade_journal'
  | 'portfolio_export_csv'
  // Charts
  | 'charts_technical_analysis'
  | 'charts_timeframe'
  | 'charts_live'
  | 'charts_synthetic'
  | 'charts_indicators'
  // Settings
  | 'settings_language'
  | 'settings_theme'
  | 'settings_paper_capital'
  | 'settings_subscription'
  | 'settings_upgrade'
  | 'settings_current_plan'
  | 'settings_manage_subscription'
  | 'settings_title'
  | 'settings_configuration'
  | 'settings_paper_trading'
  | 'settings_starting_capital'
  | 'settings_apply'
  | 'settings_capital_hint'
  | 'settings_capital_free_hint'
  | 'settings_active_strategy'
  | 'settings_strategy_hint'
  | 'settings_tracked_assets'
  | 'settings_tracked_assets_hint'
  | 'settings_tracked_assets_free_hint'
  | 'settings_appearance'
  | 'settings_dark_mode'
  | 'settings_dark_mode_hint'
  | 'settings_poll_interval'
  | 'settings_poll_interval_hint'
  | 'settings_danger_zone'
  | 'settings_reset_all'
  | 'settings_reset_all_hint'
  | 'settings_reset'
  | 'settings_all_features_unlocked'
  // Common
  | 'common_loading'
  | 'common_error'
  | 'common_no_data'
  | 'common_connected'
  | 'common_api_connected'
  | 'common_offline'
  | 'common_save'
  | 'common_cancel'
  | 'common_reset'
  | 'common_confirm'
  | 'common_paper_trading'
  | 'common_research_only'
  | 'common_notifications'
  | 'common_no_notifications'
  | 'common_read_all'
  | 'common_clear'
  // Regime
  | 'regime_risk_on'
  | 'regime_risk_off'
  | 'regime_crisis'
  | 'regime_neutral'
  | 'regime_caution'
  // Welcome interpolation
  | 'welcome_user';

type TranslationDictionary = Record<TranslationKey, string>;

const en: TranslationDictionary = {
  // Navigation
  nav_dashboard: 'Dashboard',
  nav_charts: 'Charts',
  nav_signals: 'Signals',
  nav_portfolio: 'Portfolio',
  nav_risk_guardian: 'Risk Guardian',
  nav_opportunity_radar: 'Opportunity Radar',
  nav_strategy_lab: 'Strategy Lab',
  nav_ai_chat: 'AI Chat',
  nav_markets: 'Markets',
  nav_trade_journal: 'Trade Journal',
  nav_price_alerts: 'Price Alerts',
  nav_leaderboard: 'Leaderboard',
  nav_settings: 'Settings',
  nav_social_trading: 'Social Trading',
  nav_sign_out: 'Sign Out',
  // Dashboard
  dashboard_market_overview: 'Market Overview',
  dashboard_total_value: 'Total Value',
  dashboard_total_pnl: 'Total P&L',
  dashboard_open_positions: 'Open Positions',
  dashboard_drawdown: 'Drawdown',
  dashboard_win_rate: 'Win Rate',
  dashboard_top_signals: 'Top Signals',
  dashboard_portfolio_summary: 'Portfolio Summary',
  dashboard_market_pulse: 'Market Pulse',
  dashboard_fear_greed: 'Fear & Greed',
  // Signals
  signals_active: 'Active Signals',
  signals_long: 'Long',
  signals_short: 'Short',
  signals_avg_confidence: 'Avg Confidence',
  signals_direction: 'Direction',
  signals_entry: 'Entry',
  signals_stop_loss: 'Stop Loss',
  signals_take_profit: 'Take Profit',
  signals_confidence: 'Confidence',
  signals_quality: 'Quality',
  signals_action: 'Action',
  signals_accept: 'Accept',
  signals_close: 'Close',
  signals_trade: 'Trade',
  signals_pending_orders: 'Pending Orders',
  // Portfolio
  portfolio_paper_trading_account: 'Paper Trading Account',
  portfolio_asset_allocation: 'Asset Allocation',
  portfolio_available_capital: 'Available Capital',
  portfolio_risk_score: 'Risk Score',
  portfolio_position_size: 'Position Size',
  portfolio_auto_sl_tp: 'Auto SL/TP',
  portfolio_trade_journal: 'Trade Journal',
  portfolio_export_csv: 'Export CSV',
  // Charts
  charts_technical_analysis: 'Technical Analysis',
  charts_timeframe: 'Timeframe',
  charts_live: 'Live',
  charts_synthetic: 'Synthetic',
  charts_indicators: 'Indicators',
  // Settings
  settings_language: 'Language',
  settings_theme: 'Theme',
  settings_paper_capital: 'Paper Capital',
  settings_subscription: 'Subscription',
  settings_upgrade: 'Upgrade',
  settings_current_plan: 'Current Plan',
  settings_manage_subscription: 'Manage Subscription',
  settings_title: 'Settings',
  settings_configuration: 'Configuration',
  settings_paper_trading: 'Paper Trading',
  settings_starting_capital: 'Starting Capital (USD)',
  settings_apply: 'Apply',
  settings_capital_hint: 'Resets portfolio to the new capital amount. All open positions will be closed.',
  settings_capital_free_hint: 'Max ${max} on {tier} plan.',
  settings_active_strategy: 'Active Strategy',
  settings_strategy_hint: 'Determines how signals are generated on the Signals page.',
  settings_tracked_assets: 'Tracked Assets',
  settings_tracked_assets_hint: 'Click to toggle. These assets appear on Signals and Radar pages.',
  settings_tracked_assets_free_hint: 'Free plan: {max} assets only.',
  settings_appearance: 'Appearance',
  settings_dark_mode: 'Dark Mode',
  settings_dark_mode_hint: 'Toggle between dark and light theme',
  settings_poll_interval: 'Poll Interval',
  settings_poll_interval_hint: 'How often to fetch new data from the backend',
  settings_danger_zone: 'Danger Zone',
  settings_reset_all: 'Reset All Settings',
  settings_reset_all_hint: 'Restore defaults for capital, strategy, theme, and tracked assets',
  settings_reset: 'Reset',
  settings_all_features_unlocked: 'All features unlocked',
  // Common
  common_loading: 'Loading',
  common_error: 'Error',
  common_no_data: 'No data',
  common_connected: 'Connected',
  common_api_connected: 'API Connected',
  common_offline: 'Offline',
  common_save: 'Save',
  common_cancel: 'Cancel',
  common_reset: 'Reset',
  common_confirm: 'Confirm',
  common_paper_trading: 'Paper Trading',
  common_research_only: 'RESEARCH ONLY',
  common_notifications: 'Notifications',
  common_no_notifications: 'No notifications yet',
  common_read_all: 'Read all',
  common_clear: 'Clear',
  // Regime
  regime_risk_on: 'Risk On',
  regime_risk_off: 'Risk Off',
  regime_crisis: 'Crisis',
  regime_neutral: 'Neutral',
  regime_caution: 'Caution',
  // Welcome
  welcome_user: 'Welcome, {name}!',
};

const de: TranslationDictionary = {
  // Navigation
  nav_dashboard: 'Dashboard',
  nav_charts: 'Charts',
  nav_signals: 'Signale',
  nav_portfolio: 'Portfolio',
  nav_risk_guardian: 'Risiko-Schutz',
  nav_opportunity_radar: 'Chancen-Radar',
  nav_strategy_lab: 'Strategie-Labor',
  nav_ai_chat: 'KI-Chat',
  nav_markets: 'M\u00e4rkte',
  nav_trade_journal: 'Handelsjournal',
  nav_price_alerts: 'Preisalarme',
  nav_leaderboard: 'Bestenliste',
  nav_settings: 'Einstellungen',
  nav_social_trading: 'Social Trading',
  nav_sign_out: 'Abmelden',
  // Dashboard
  dashboard_market_overview: 'Markt\u00fcbersicht',
  dashboard_total_value: 'Gesamtwert',
  dashboard_total_pnl: 'Gesamt-GuV',
  dashboard_open_positions: 'Offene Positionen',
  dashboard_drawdown: 'Drawdown',
  dashboard_win_rate: 'Gewinnquote',
  dashboard_top_signals: 'Top-Signale',
  dashboard_portfolio_summary: 'Portfolio-\u00dcbersicht',
  dashboard_market_pulse: 'Marktpuls',
  dashboard_fear_greed: 'Angst & Gier',
  // Signals
  signals_active: 'Aktive Signale',
  signals_long: 'Long',
  signals_short: 'Short',
  signals_avg_confidence: 'Durchschn. Konfidenz',
  signals_direction: 'Richtung',
  signals_entry: 'Einstieg',
  signals_stop_loss: 'Stop Loss',
  signals_take_profit: 'Take Profit',
  signals_confidence: 'Konfidenz',
  signals_quality: 'Qualit\u00e4t',
  signals_action: 'Aktion',
  signals_accept: 'Annehmen',
  signals_close: 'Schlie\u00dfen',
  signals_trade: 'Handeln',
  signals_pending_orders: 'Offene Auftr\u00e4ge',
  // Portfolio
  portfolio_paper_trading_account: 'Papierhandel-Konto',
  portfolio_asset_allocation: 'Verm\u00f6gensaufteilung',
  portfolio_available_capital: 'Verf\u00fcgbares Kapital',
  portfolio_risk_score: 'Risikobewertung',
  portfolio_position_size: 'Positionsgr\u00f6\u00dfe',
  portfolio_auto_sl_tp: 'Auto SL/TP',
  portfolio_trade_journal: 'Handelsjournal',
  portfolio_export_csv: 'CSV exportieren',
  // Charts
  charts_technical_analysis: 'Technische Analyse',
  charts_timeframe: 'Zeitrahmen',
  charts_live: 'Live',
  charts_synthetic: 'Synthetisch',
  charts_indicators: 'Indikatoren',
  // Settings
  settings_language: 'Sprache',
  settings_theme: 'Design',
  settings_paper_capital: 'Papierhandel-Kapital',
  settings_subscription: 'Abonnement',
  settings_upgrade: 'Upgrade',
  settings_current_plan: 'Aktueller Plan',
  settings_manage_subscription: 'Abonnement verwalten',
  settings_title: 'Einstellungen',
  settings_configuration: 'Konfiguration',
  settings_paper_trading: 'Papierhandel',
  settings_starting_capital: 'Startkapital (USD)',
  settings_apply: '\u00dcbernehmen',
  settings_capital_hint: 'Setzt das Portfolio auf den neuen Kapitalbetrag zur\u00fcck. Alle offenen Positionen werden geschlossen.',
  settings_capital_free_hint: 'Max. ${max} im {tier}-Plan.',
  settings_active_strategy: 'Aktive Strategie',
  settings_strategy_hint: 'Bestimmt, wie Signale auf der Signale-Seite generiert werden.',
  settings_tracked_assets: 'Verfolgte Assets',
  settings_tracked_assets_hint: 'Klicken zum Umschalten. Diese Assets erscheinen auf den Signale- und Radar-Seiten.',
  settings_tracked_assets_free_hint: 'Kostenloser Plan: nur {max} Assets.',
  settings_appearance: 'Darstellung',
  settings_dark_mode: 'Dunkler Modus',
  settings_dark_mode_hint: 'Zwischen dunklem und hellem Design wechseln',
  settings_poll_interval: 'Aktualisierungsintervall',
  settings_poll_interval_hint: 'Wie oft neue Daten vom Backend abgerufen werden',
  settings_danger_zone: 'Gefahrenzone',
  settings_reset_all: 'Alle Einstellungen zur\u00fccksetzen',
  settings_reset_all_hint: 'Standardwerte f\u00fcr Kapital, Strategie, Design und verfolgte Assets wiederherstellen',
  settings_reset: 'Zur\u00fccksetzen',
  settings_all_features_unlocked: 'Alle Funktionen freigeschaltet',
  // Common
  common_loading: 'Laden',
  common_error: 'Fehler',
  common_no_data: 'Keine Daten',
  common_connected: 'Verbunden',
  common_api_connected: 'API verbunden',
  common_offline: 'Offline',
  common_save: 'Speichern',
  common_cancel: 'Abbrechen',
  common_reset: 'Zur\u00fccksetzen',
  common_confirm: 'Best\u00e4tigen',
  common_paper_trading: 'Papierhandel',
  common_research_only: 'NUR FORSCHUNG',
  common_notifications: 'Benachrichtigungen',
  common_no_notifications: 'Noch keine Benachrichtigungen',
  common_read_all: 'Alle lesen',
  common_clear: 'L\u00f6schen',
  // Regime
  regime_risk_on: 'Risiko an',
  regime_risk_off: 'Risiko aus',
  regime_crisis: 'Krise',
  regime_neutral: 'Neutral',
  regime_caution: 'Vorsicht',
  // Welcome
  welcome_user: 'Willkommen, {name}!',
};

export const translations: Record<Locale, TranslationDictionary> = { en, de };

/**
 * Translate a key to the given locale with optional interpolation.
 *
 * Usage:
 *   t('welcome_user', 'de', { name: 'Mike' })  // "Willkommen, Mike!"
 *   t('nav_dashboard', 'de')                    // "Dashboard"
 */
export function t(
  key: TranslationKey,
  locale: Locale,
  vars?: Record<string, string | number>,
): string {
  let text = translations[locale]?.[key] ?? translations.en[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
    }
  }
  return text;
}
