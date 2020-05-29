# Evaluation Infrastructure for Aardwolf

## Usage

### Localization Effectiveness

* Extract [Siemens data](https://sir.csc.ncsu.edu/) into a directory. It must contain individual `tar.gz` archives for all subject programs in expected versions.
* If you want to overwrite plugins used by default, put `plugins.yml` (only with Aardwolf `plugins` item) to `<path to results>`.

```shell
docker run \
    --volume <path to aardwolf>:/mnt/aardwolf \
    --volume <path to results>:/mnt/results \
    --volume <path to siemens>:/mnt/siemens \
    aardwolf_eval effectiveness
```

* Use `results_effectiveness` directory if you want to proceed with analysis notebooks from `analysis/`.

### Scalability

* If you want to overwrite plugins used by default, put `plugins.yml` (only with Aardwolf `plugins` item) to `<path to results>`.

```shell
docker run \
    --volume <path to aardwolf>:/mnt/aardwolf \
    --volume <path to results>:/mnt/results \
    aardwolf_eval scalability
```

* Use `results_scalability` directory if you want to proceed with analysis notebooks from `analysis/`.

## Troubleshooting

#### echo: write error: No space left on device

Running the experiments requires a lot of disk space for temporary data.
If you run to the issue of insufficient space and you have a different partition with more space,
you can use `--volume <path to workdir>:/mnt/workdir` to specify the working directory.
