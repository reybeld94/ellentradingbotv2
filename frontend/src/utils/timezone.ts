const DEFAULT_LOCALE = 'en-US';
const DEFAULT_TZ = 'America/New_York';

const { toLocaleString, toLocaleDateString, toLocaleTimeString } = Date.prototype as unknown as {
  toLocaleString: typeof Date.prototype.toLocaleString;
  toLocaleDateString: typeof Date.prototype.toLocaleDateString;
  toLocaleTimeString: typeof Date.prototype.toLocaleTimeString;
};

Date.prototype.toLocaleString = function (locale?: string | string[], options?: Intl.DateTimeFormatOptions) {
  return toLocaleString.call(this, locale ?? DEFAULT_LOCALE, { timeZone: DEFAULT_TZ, ...(options ?? {}) });
};

Date.prototype.toLocaleDateString = function (locale?: string | string[], options?: Intl.DateTimeFormatOptions) {
  return toLocaleDateString.call(this, locale ?? DEFAULT_LOCALE, { timeZone: DEFAULT_TZ, ...(options ?? {}) });
};

Date.prototype.toLocaleTimeString = function (locale?: string | string[], options?: Intl.DateTimeFormatOptions) {
  return toLocaleTimeString.call(this, locale ?? DEFAULT_LOCALE, { timeZone: DEFAULT_TZ, ...(options ?? {}) });
};

export {};
