export default class LiveBrokerDataSource {
  private log = import.meta.env.VITE_LOG_BROKER_WIRE === 'true';
  private useLive = import.meta.env.VITE_USE_LIVE_BROKER === 'true';

  private dbg(...args: any[]) {
    if (this.log) console.debug('[broker]', ...args);
  }

  handleAccountUpdate(mapped: any) {
    // Previously: console.debug('broker:account', mapped)
    this.dbg('account', mapped);
  }
}
