#include <iostream>
#include "SnapPea.h"
#include "hp_Dirichlet.h"

using std::cout;
using std::endl;

#include "examples/K13a1779.h"

void qdprint(qd_real x);
void load_moebius(COMPLEX *coeffs, hp_MoebiusTransformation *M);
void print_moebius(hp_MoebiusTransformation *M);
void print_o31(hp_O31Matrix O);

extern hp_WEPolyhedron  *hp_Dirichlet_from_generators(
    hp_O31Matrix            generators[],
    int                     num_generators,
    REAL                    vertex_epsilon,
    DirichletInteractivity  interactivity,
    Boolean                 maximize_injectivity_radius);

int main() {
  char output[200];
  unsigned int oldcw;
  hp_MoebiusTransformation M[2];
  hp_O31Matrix generators[2];
  hp_WEPolyhedron* P;
  COMPLEX det;
  Boolean check;
  int i, j;

  fpu_fix_start(&oldcw);

  load_moebius(A_coeffs, &M[0]);
  load_moebius(B_coeffs, &M[1]);
  hp_Moebius_array_to_O31_array(M, generators, 2);

  /***
  cout << "Moebius transformation A:" << endl;
  print_moebius(&M[0]);
  det = hp_sl2c_determinant(M[0].matrix);
  cout << "determinant: " << det.real() << "+ i*" << det.imag() << endl;
  //  hp_Moebius_to_O31(&M[0], generators[0]);
  print_o31(generators[0]);

  cout << "Moebius transformation B:" << endl;
  print_moebius(&M[1]);
  det = hp_sl2c_determinant(M[1].matrix);
  cout << "determinant: " << det.real() << "+ i*" << det.imag() << endl;
  print_o31(generators[1]);

  check = hp_O31_determinants_OK(generators, 2, (REAL)"1.0e-55");
  if (check)
    cout << "determinants look OK" << endl;
  else
    cout << "determinants look bad" << endl;
  cout << "gen 0: ";
  qdprint(hp_gl4R_determinant(generators[0]));
  cout << endl << "gen 1: ";
  qdprint(hp_gl4R_determinant(generators[1]));
  cout << endl;
  **/

  P = hp_Dirichlet_from_generators(generators, 2, (REAL)"1.0e-24", 0, 1);
  cout << P->num_vertices << " vertices" << endl;
  cout << P->num_edges << " edges" << endl;
  cout << P->num_faces << " faces" << endl;
 
  fpu_fix_end(&oldcw);
  return 0;
}

void qdprint(qd_real x) {
  char buffer[100];
  x.write(buffer, 100, 68);
  cout << buffer << endl;
}

void load_moebius(COMPLEX *coeffs, hp_MoebiusTransformation *M) {
  M->matrix[0][0] = coeffs[0];
  M->matrix[0][1] = coeffs[1];
  M->matrix[1][0] = coeffs[2];
  M->matrix[1][1] = coeffs[3];
  M->parity = orientation_preserving;
}

void print_moebius(hp_MoebiusTransformation *M) {
  int i, j;
  for (i=0; i<2; i++)
    for (j=0;j<2;j++){
      qdprint(M->matrix[i][j].real());
      cout << " + i ";
      qdprint(M->matrix[i][j].imag());
      cout << endl;
    }
}

void print_o31(hp_O31Matrix O) {
  int i, j;
  for (i=0; i<4; i++)
    for (j=0;j<4;j++){
      qdprint(O[i][j]);
    }
}

#if 0
  // for (i=0; i<2; i++)
  //   for (j=0;j<2;j++){
  //     qdprint(A[i][j].real());
  //     cout << " + i ";
  //     qdprint(A[i][j].imag());
  //     cout << endl;
  //   }

//  for (i=0; i<2; i++)
//    for (j=0;j<2;j++){
//      qdprint(B[i][j].real());
//      cout << " + i";
//      qdprint(B[i][j].imag());
//      cout << endl;
//    }

//  hp_sl2c_copy(M.matrix, A);

  // for (i=0; i<2; i++)
  //   for (j=0;j<2;j++){
  //     qdprint(M.matrix[i][j].real());
  //     cout << " + i";
  //     qdprint(M.matrix[i][j].imag());
  //     cout << endl;
  //   }

  // M.parity = orientation_preserving;




K13n3393

COMPLEX A_coeffs[4] = {
  {.real="-0.294775307001479316651602297792426985784092671339204294140277450891400723079378553577126592761609372305822", .imag="1.19891135137122116945811367023160467416726346695857852055013193673313072339600476967213939093231064881563"},
  {.real="-0.800381602529112007134454251704115051628665476773279379591154958884030863852718264295707421722568895605785", .imag="0.667523834192674228532050832085763101142412585817168757176579231417310949098098183612666654132227988416719"},
  {.real="0.800381602529112007134454251704115051628665476773279379591154958884030863852718264295707421722568895605792", .imag="0.667523834192674228532050832085763101142412585817168757176579231417310949098098183612666654132227988416738"},
  {.real="-0.996129569112455086854971346859047667450727741293203326495937624340740435473676519775334587512905600641974", .imag="-0.426506062700140423677170206257508634071941573701944458018601441076236812265604926082701195101462603208063"}
};

  A[0][0] = [{.real="-0.294775307001479316651602297792426985784092671339204294140277450891400723079378553577126592761609372305822", .imag="1.19891135137122116945811367023160467416726346695857852055013193673313072339600476967213939093231064881563"};
  A[0][1] = {.real="-0.800381602529112007134454251704115051628665476773279379591154958884030863852718264295707421722568895605785", .imag="0.667523834192674228532050832085763101142412585817168757176579231417310949098098183612666654132227988416719"};
  A[1][0] = {.real="0.800381602529112007134454251704115051628665476773279379591154958884030863852718264295707421722568895605792", .imag="0.667523834192674228532050832085763101142412585817168757176579231417310949098098183612666654132227988416738"};
  A[1][1] = {.real="-0.996129569112455086854971346859047667450727741293203326495937624340740435473676519775334587512905600641974", .imag="-0.426506062700140423677170206257508634071941573701944458018601441076236812265604926082701195101462603208063"};

  A = {
    {{.real="-0.294775307001479316651602297792426985784092671339204294140277450891400723079378553577126592761609372305822", .imag = "1.19891135137122116945811367023160467416726346695857852055013193673313072339600476967213939093231064881563"}, {.real = "-0.800381602529112007134454251704115051628665476773279379591154958884030863852718264295707421722568895605785"; .imag = "-0.667523834192674228532050832085763101142412585817168757176579231417310949098098183612666654132227988416719";

  A[1][0] = {.real="0.800381602529112007134454251704115051628665476773279379591154958884030863852718264295707421722568895605792", .imag = "0.667523834192674228532050832085763101142412585817168757176579231417310949098098183612666654132227988416738"};

  A[1][1] = {.real="-0.996129569112455086854971346859047667450727741293203326495937624340740435473676519775334587512905600641974", .imag="-0.426506062700140423677170206257508634071941573701944458018601441076236812265604926082701195101462603208063"};


B = [1.34847044983027047478232958722882685468010551394772042721450375858268705417545503325280700703748444087103 + 1.42275808780909248405696106061955446784960703896033402613488891258034491582745714352951789807857344500895*I,

-0.182109256507086655559150239515619244276040855409701906321335537269679739881308999302302597662457420508596 - 1.87691267012514471746772117557906527691431667122485889689561330486058985112395960515204922779941255280423*I,

1.77199883971215360799743899301349860112462365542091142479924637026622022339999502507448146930510986447778 + 1.95822030561140116800597090613074402282067630613344490863750861748811166253030606998017081203259097635024*I,

0.164002914512037018900183105802103087495750201210779241971092747710325525093238089173511916650110973533479 - 2.90390760225699535574910891088768826054459227856084182159113541063836267583867512729425067881495403781811*I]



#endif
