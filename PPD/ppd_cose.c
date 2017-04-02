
/* Compilation:
   $ gcc ppd_cose.c -ltiff
*/



#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <tiffio.h>
#include <libgen.h>

#define S 4


// {{{ matrix_alloc()
int **matrix_alloc(size_t cols, size_t rows)
{
	int i, j;
	int **m = (int**)malloc(sizeof(m) * cols);
	if(!m) 
	{
		perror("out of memory (cols)");
		return NULL;
	}

	for(i=0; i<cols; i++)
	{
		m[i] = (int*)malloc(sizeof(m[i]) * rows);
		if(!m[i])
		{
			perror("out of memory (rows)");
			return NULL;
		}
	}

	for(j=0; j<rows; j++)
		for(i=0; i<cols; i++)
			m[i][j]=0;

	return m;
}
// }}}

// {{{ matrix_free()
void matrix_free(int **m, size_t cols, size_t rows)
{
	int x;
	for(x=0; x<cols; x++)
		free(m[x]);
	free(m);
}
// }}}

// {{{ matrix_copy()
void matrix_copy(int **mdst, int **msrc, size_t cols, size_t rows)
{
	int i, j;
	for(j=0; j<rows; j++)
	{
		for(i=0; i<cols; i++)
		{
			mdst[i][j] = msrc[i][j];
		}
	}
}
// }}}

// {{{ message_hide_random_br()
// Hide a random message with especified bitrate
void message_hide_random_br(
	int **matrix, size_t cols, size_t rows, float bitrate)
{
	int br=1/bitrate;
	int i, j;
	for(j=0; j<rows; j++)
	{
		for(i=0; i<cols; i++)
		{
			if((matrix[i][j]<255)&&(matrix[i][j]>0))
			{
				//  0 or 1?
				int bit = rand()%2;

				// + or -?
				int s = -1;
				if(rand()%2==0)
					s = 1;

				// Bit insertion
				if(rand()%br==0) 
				{
					if(bit==0 && matrix[i][j]%2==1)
						matrix[i][j] += s;

					if(bit==1 && matrix[i][j]%2==0)
						matrix[i][j] += s;
				}
			}
		}
	}
}
// }}}

// {{{ count_patterns()
void count_patterns(int shapes[S][S][S][S], int **I, int cols, int rows)
{
	int i, j, k, l, x, y;

	// initialize shapes
	for(i=0; i<S; i++)
		for(j=0; j<S; j++)
			for(k=0; k<S; k++)
				for(l=0; l<S; l++)
					shapes[i][j][k][l]=0;

	// a b
	// c d
	// . e

	//    c1 c2
	//     \ /
	//  l - m - r

	for(y=1; y<rows-1; y++)
	{
		for(x=0; x<cols-1; x++)
		{
			int _a = I[x][y-1];
			int _b = I[x+1][y-1];
			int _c = I[x][y];
			int _d = I[x+1][y];
			int _e = I[x+1][y+1];

			int l=0, r=0, c1=0, c2=0;
			int mn = 256;
			int mx=0;
			if(_a<mn) { mn=_a; l=_b; r=_c; c1=_d; c2=_e; }
			if(_b<mn) { mn=_b; l=_d; r=_a; c1=_c; c2=_e; }
			if(_c<mn) { mn=_c; l=_a; r=_e; c1=_b; c2=_d; }
			if(_d<mn) { mn=_d; l=_e; r=_b; c1=_c; c2=_a; }
			if(_e<mn) { mn=_e; l=_c; r=_d; c1=_a; c2=_b; }

			int i1 = (l-mn>=S?S-1:l-mn);
			int i2 = (c1-mn>=S?S-1:c1-mn);
			int i3 = (c2-mn>=S?S-1:c2-mn);
			int i4 = (r-mn>=S?S-1:r-mn);
	
			shapes[i1][i2][i3][i4]++;

			if(_a>mx) { mx = _a; l=_b; r=_c; c1=_d; c2=_e; }
			if(_b>mx) { mx = _b; l=_d; r=_a; c1=_c; c2=_e; }
			if(_c>mx) { mx = _c; l=_a; r=_e; c1=_b; c2=_d; }
			if(_d>mx) { mx = _d; l=_e; r=_b; c1=_c; c2=_a; }
			if(_e>mx) { mx = _e; l=_c; r=_d; c1=_a; c2=_b; }

			i1 = (mx-l>=S?S-1:mx-l);
			i2 = (mx-c1>=S?S-1:mx-c1);
			i3 = (mx-c2>=S?S-1:mx-c2);
			i4 = (mx-r>=S?S-1:mx-r);

			shapes[i1][i2][i3][i4]++;
		}
	}

}
// }}}


int main(int argc, char* argv[])
{
	uint32 rows;
	tsize_t cols;
	tdata_t buf;
	uint32 x;
	uint32 y;


	if(argc!=2)
	{
		printf("Usage: %s <input tiff file>\n", argv[0]);
		return -1;
	}

	srand(time(NULL));
	//srand(0);

	TIFF* tif_i = TIFFOpen(argv[1], "r");
	if (!tif_i) 
	{
		printf("Error reading Tiff image\n");
		return -1;
	}

	TIFFGetField(tif_i, TIFFTAG_IMAGELENGTH, &rows);
	cols = TIFFScanlineSize(tif_i);
	buf = _TIFFmalloc(cols);


	// Matrix I
	int **I = matrix_alloc(cols, rows);

	for (y = 0; y < rows; y++)
	{
		TIFFReadScanline(tif_i, buf, y, 0);
		for (x = 0; x < cols; x++)
		{
			unsigned char *bytes = buf;
			I[x][y]=bytes[x];
		}
	}

	_TIFFfree(buf);
	TIFFClose(tif_i);


	int i, j, k, l;
	

	int shapes[S][S][S][S];
	int shapes_s[S][S][S][S];
	

	// Create Is, inserting a random message
	int **Is = matrix_alloc(cols, rows);
	matrix_copy(Is, I, cols, rows);
	message_hide_random_br(Is, cols, rows, 1);


	count_patterns(shapes, I, cols, rows);
	count_patterns(shapes_s, Is, cols, rows);


	float R[S*S*S*S];
	float mx=0;
	float mn=10;
	int idx=0;

	for(i=0; i<S; i++)
		for(j=0; j<S; j++)
			for(k=0; k<S; k++)
				for(l=0; l<S; l++)
			{

				float f=0;
				float cover = (float)shapes[i][j][k][l];
				float stego = (float)shapes_s[i][j][k][l];


				if(cover>0)
					f = stego / cover;

				if(f>mx) mx=f;
				if(f<mn) mn=f;

				R[idx++]=f;
			}

	for(i=0; i<idx; i++)
		printf("%f ", (R[i]-mn)/(mx-mn));


	printf("%s\n", basename(argv[1]));

	matrix_free(I, cols, rows);
	matrix_free(Is, cols, rows);

	return 0;
}


	 



