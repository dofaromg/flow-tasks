'use strict';

exports.now = () => new Date().toISOString();

exports.addDays = (days) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
};

exports.addMonths = (months) => {
  const d = new Date();
  d.setMonth(d.getMonth() + months);
  return d.toISOString();
};

exports.isPast = (isoStr) => new Date(isoStr) < new Date();
