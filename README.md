# quoco

My toy platform for time-based documents built on my toy object filesystem, [quocofs](https://github.com/vinhowe/quocofs).

## installation

Assuming an updated version of Rust (I'm on 1.51.0 as of writing) and Python 3.9 minimum, just run:
```sh
pip install git+https://github.com/vinhowe/quoco.git
```

For now you'll need a GCP service account JSON file at `(~/.config|$XDG_CONFIG_HOME)/quoco/google-service-account.json`,
with access to a Google Storage bucket named `quocofs`.


## todo

- [ ] Come up with usage example(s)
