build:
	cargo build --release

test:
	tmux kill-session -t shf > /dev/null 2>&1 || >&2
	tmux new-session -s shf -d && python3 test/test_shf.py --verbose && tmux kill-session -t shf

bump-major:
	bump2version major

bump-minor:
	bump2version minor

bump-patch:
	bump2version patch

release-major: build bump-major
release-minor: build bump-minor
release-patch: build bump-patch

.PHONY: \
	build \
	test \
