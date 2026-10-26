/** 7672 -> "7.7 GW" */
export const gw = (mw: number, digits = 1) => `${(mw / 1000).toFixed(digits)} GW`

/** 1290 -> "+1.3 GW", -426 -> "-0.4 GW" */
export const signedGw = (mw: number, digits = 1) => `${mw > 0 ? '+' : ''}${gw(mw, digits)}`

/** 0.1008 -> "10%" */
export const percent = (share: number) => `${Math.round(share * 100)}%`
