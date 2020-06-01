#define _GNU_SOURCE

#include <err.h>
#include <stdio.h>
#include <stdlib.h>

#include <drpm.h>

static void
read_drpm(const char * const filename)
{
	drpm *delta = NULL;
	int res = drpm_read(&delta, filename);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_read() failed for %s: %s",
		    filename, drpm_strerror(res));
	if (delta == NULL)
		errx(1, "drpm_read() returned a null delta for %s", filename);

	unsigned type;
	res = drpm_get_uint(delta, DRPM_TAG_TYPE, &type);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_get_uint(DRPM_TAG_TYPE) failed for %s: %s",
		    filename, drpm_strerror(res));

	res = drpm_destroy(&delta);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_destroy() failed for %s: %s",
		    filename, drpm_strerror(res));

	puts(type == DRPM_TYPE_STANDARD ? "standard" : "rpm-only");
}

int main(const int argc, const char * const argv[])
{
	if (argc != 4)
		errx(1, "Usage: examine old.rpm new.rpm tempdir");
	const char * const oldfile = argv[1];
	const char * const newfile = argv[2];
	const char * const tempd = argv[3];

	char *outfile;
	if (asprintf(&outfile, "%s/noopt.rpm", tempd) < 0 || outfile == NULL)
		err(1, "Could not build the noopt.rpm filename");

	puts("make standard");
	int res = drpm_make(oldfile, newfile, outfile, NULL);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_make(noopt) failed: %s",
		    drpm_strerror(res));
	puts("read standard");
	read_drpm(outfile);

	puts("make options");
	drpm_make_options *opts;
	res = drpm_make_options_init(&opts);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_make_options_init() failed: %s",
		    drpm_strerror(res));
	res = drpm_make_options_defaults(opts);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_make_options_defaults() failed: %s",
		    drpm_strerror(res));
	res = drpm_make_options_set_type(opts, DRPM_TYPE_RPMONLY);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_make_options_set_type(RPMONLY) failed: %s",
		    drpm_strerror(res));

	free(outfile);
	if (asprintf(&outfile, "%s/only.rpm", tempd) < 0 || outfile == NULL)
		err(1, "Could not build the only.rpm filename");

	puts("make rpm-only");
	res = drpm_make(oldfile, newfile, outfile, opts);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_make(only) failed: %s",
		    drpm_strerror(res));
	puts("read rpm-only");
	read_drpm(outfile);

	res = drpm_make_options_destroy(&opts);
	if (res != DRPM_ERR_OK)
		errx(1, "drpm_make_options_destroy() failed: %s",
		    drpm_strerror(res));

	puts("fine");
	return 0;
}
