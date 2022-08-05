build:
	cargo build --release

test:
	tmux kill-session -t shf > /dev/null 2>&1 || >&2
	tmux new-session -s shf -d && python3 test/test_shf.py --verbose && tmux kill-session -t shf

release-major:
	bump2version major

release-minor:
	bump2version minor

release-patch:
	bump2version patch

.PHONY: \
	test \
