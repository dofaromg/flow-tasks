# DL580 Signing Service Contract

This directory contains the signing interface contract only. It does not contain private key material and does not implement network mutation.

Production rule: Workers ask DL580 for signed origin results. DL580 signs. Edge code verifies and records `origin_signature`.
