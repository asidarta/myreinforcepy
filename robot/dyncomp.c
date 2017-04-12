#include "rtl_inc.h"

#include "ruser.h"
#include "robdecls.h"

#include "userfn.h"
#include <stdlib.h>


/* 
 Uncomment these and insert in the dyncomp subroutine
 c1 =   0.381312991268 + (  0.022403160044)*uu + ( -0.082130896031)*vv + ( -0.114696885729)*uuvv;
 c2 =   0.226195316709 + (  0.003730297846)*uu + ( -0.082218580821)*vv + (  0.001328935119)*uuvv;
 c3 =   0.224570748884 + (  0.023143420584)*uu + ( -0.094454303916)*vv + (  0.299434548164)*uuvv;
*/
#define home_trained 1

#ifdef home_trained

void   neuralnetcorrection(double *inp, double *out)
{
/* This code piece  was automatically generated by writenetcode.m (matlab) */
   int i; 
   double o_a[6], o_b[7] ;

    o_a[ 0] =  -0.07675201 * inp[ 0] +0.17485044 * inp[ 1] -0.00429268 * inp[ 2] +0.00308595 * inp[ 3] -0.00306219 * inp[ 4] -0.01934473 * inp[ 5] -2.30074831;
    o_a[ 1] =  -0.04011421 * inp[ 0] +0.67783407 * inp[ 1] -0.27341711 * inp[ 2] +0.08065918 * inp[ 3] -0.00041399 * inp[ 4] -0.07563371 * inp[ 5] -2.01282500;
    o_a[ 2] =  -0.08944420 * inp[ 0] +0.07380647 * inp[ 1] +0.25535992 * inp[ 2] -0.04778657 * inp[ 3] -0.05169960 * inp[ 4] +0.10050731 * inp[ 5] -0.07709626;
    o_a[ 3] =  -0.09003267 * inp[ 0] +0.11481986 * inp[ 1] +0.09507574 * inp[ 2] +0.00353351 * inp[ 3] -0.00211657 * inp[ 4] -0.00492585 * inp[ 5] -1.00079390;
    o_a[ 4] =  +1.19299135 * inp[ 0] -0.43276404 * inp[ 1] +2.97130898 * inp[ 2] +0.35185227 * inp[ 3] -0.05678326 * inp[ 4] -0.01731679 * inp[ 5] +2.63312644;
    o_a[ 5] =  -0.16192048 * inp[ 0] +0.17160096 * inp[ 1] -0.00457998 * inp[ 2] +0.32174581 * inp[ 3] -0.01909285 * inp[ 4] +0.02115276 * inp[ 5] -0.76082428;

    for (i=0; i< 6;i++) o_a[i] = 2.0/(1+exp(-2*o_a[i])) - 1.0;

    o_b[ 0] =  +9.70942012 * o_a[0] +0.49761243 * o_a[1] +1.38844103 * o_a[2] -8.76284555 * o_a[3] +0.13747180 * o_a[4] +0.79090439 * o_a[5] +4.19396245;
    o_b[ 1] =  +8.27261659 * o_a[0] +2.96857424 * o_a[1] +3.03259258 * o_a[2] +0.11152304 * o_a[3] -0.29391523 * o_a[4] +0.57423945 * o_a[5] +7.15359236;
    o_b[ 2] =  -0.85247352 * o_a[0] +0.13664729 * o_a[1] -0.04382099 * o_a[2] +0.94929127 * o_a[3] -0.03084266 * o_a[4] -0.03933239 * o_a[5] -0.44895962;
    o_b[ 3] =  +2.00437877 * o_a[0] +0.30640844 * o_a[1] +1.05958064 * o_a[2] +0.57307500 * o_a[3] -0.47850996 * o_a[4] -3.58966221 * o_a[5] +1.70503604;
    o_b[ 4] =  +6.74766051 * o_a[0] +0.53823703 * o_a[1] +0.16206012 * o_a[2] +1.80833798 * o_a[3] -0.16380983 * o_a[4] +0.19656606 * o_a[5] +7.10593494;
    o_b[ 5] =  -3.70940544 * o_a[0] -0.47998055 * o_a[1] -0.18216319 * o_a[2] -1.25764054 * o_a[3] +0.12793357 * o_a[4] -0.12355957 * o_a[5] -4.29784631;
    o_b[ 6] =  -6.80414926 * o_a[0] -2.48433237 * o_a[1] +1.20686213 * o_a[2]+35.63528025 * o_a[3] +0.21911684 * o_a[4]-11.97743409 * o_a[5]+11.25166683;

    for (i=0; i< 7;i++) o_b[i] = 2.0/(1+exp(-2*o_b[i])) - 1.0;

    out[ 0] =  +1.30232066 * o_b[0] +0.82495608 * o_b[1]+22.71248988 * o_b[2] -0.14941262 * o_b[3] +0.27449890 * o_b[4] +9.33933675 * o_b[5] +0.22165855 * o_b[6] +5.32960667;
    out[ 1] =  -0.39197259 * o_b[0] -0.79251715 * o_b[1] -0.51565484 * o_b[2] -0.43288757 * o_b[3] -6.68172637 * o_b[4]-11.55073011 * o_b[5] -0.20858446 * o_b[6] -3.25195052;


}

#else

void   neuralnetcorrection(double *inp, double *out)
{
/* This code piece  was automatically generated by writenetcode.m (matlab) */
   int i; 
   double o_a[10], o_b[7] ;

    o_a[ 0] =  -2.71389436 * inp[ 0] -1.68863595 * inp[ 1] -3.19482768 * inp[ 2] +3.11501374 * inp[ 3] -1.17876293 * inp[ 4] +4.35764401 * inp[ 5] -3.20401765 * inp[ 6]+30.93551918 * inp[ 7] +8.24954849 * inp[ 8]+27.29521199 * inp[ 9] +8.46742238;
    o_a[ 1] =  -0.47131485 * inp[ 0] +0.79056300 * inp[ 1] -2.82358506 * inp[ 2] +2.69910772 * inp[ 3] +0.06576588 * inp[ 4] +0.13250988 * inp[ 5] -0.01835922 * inp[ 6] +1.03735566 * inp[ 7] -0.88179437 * inp[ 8] +0.49454812 * inp[ 9] -3.27151452;
    o_a[ 2] =  -0.29609765 * inp[ 0] +0.14535879 * inp[ 1] +0.13219654 * inp[ 2] -0.02612857 * inp[ 3] +0.00665205 * inp[ 4] +0.00916937 * inp[ 5] +0.00111977 * inp[ 6] +0.09919788 * inp[ 7] -0.10353335 * inp[ 8] -0.53817087 * inp[ 9] +0.54919663;
    o_a[ 3] =  +7.59933696 * inp[ 0] +0.07970013 * inp[ 1] -9.10357759 * inp[ 2] +9.50575553 * inp[ 3] +5.16540438 * inp[ 4] +3.62602572 * inp[ 5] -3.41529553 * inp[ 6] -2.18082865 * inp[ 7]-11.31172844 * inp[ 8] -5.07357620 * inp[ 9]+18.63743047;
    o_a[ 4] =  +0.32043160 * inp[ 0] -0.19693638 * inp[ 1] -0.06043597 * inp[ 2] -0.16497414 * inp[ 3] -0.01212951 * inp[ 4] +0.00340801 * inp[ 5] -0.00154586 * inp[ 6] -0.12182198 * inp[ 7] +0.15883016 * inp[ 8] -0.11115088 * inp[ 9] +0.85974188;
    o_a[ 5] =  -0.52346265 * inp[ 0] +1.77829736 * inp[ 1] -2.04139854 * inp[ 2] +4.03251312 * inp[ 3] -1.97146416 * inp[ 4] -0.85206904 * inp[ 5] +0.54538016 * inp[ 6]-25.11824374 * inp[ 7]+31.99927518 * inp[ 8]+44.33530612 * inp[ 9] -2.62583999;
    o_a[ 6] =  +0.76883000 * inp[ 0] -0.74316709 * inp[ 1] +0.05722137 * inp[ 2] +0.10551575 * inp[ 3] -0.04221429 * inp[ 4] +0.01319868 * inp[ 5] -0.00587782 * inp[ 6] -0.12355518 * inp[ 7] +0.77977488 * inp[ 8] +0.75080357 * inp[ 9] +4.00288494;
    o_a[ 7] =  +3.29792537 * inp[ 0] -7.62337520 * inp[ 1] +0.98478919 * inp[ 2] +0.96269064 * inp[ 3] +0.71898007 * inp[ 4] -0.96777069 * inp[ 5] +0.04833879 * inp[ 6] +0.98420585 * inp[ 7] -8.89038925 * inp[ 8] -0.37101973 * inp[ 9]+33.70530145;
    o_a[ 8] =  -1.80392623 * inp[ 0] +1.00090879 * inp[ 1] +0.44159534 * inp[ 2] +0.19413570 * inp[ 3] +0.09378403 * inp[ 4] +0.09238195 * inp[ 5] -0.00389026 * inp[ 6] +1.06423249 * inp[ 7] -0.87120180 * inp[ 8] -3.97651902 * inp[ 9] -4.43983975;
    o_a[ 9] = -27.25683016 * inp[ 0] -8.61972571 * inp[ 1] -4.92577585 * inp[ 2]+11.46608285 * inp[ 3] +5.14409528 * inp[ 4] -4.39269065 * inp[ 5] +0.01125334 * inp[ 6]-15.78524967 * inp[ 7] -1.04470663 * inp[ 8] -1.52258000 * inp[ 9]+25.36770914;

    for (i=0; i<10;i++) o_a[i] = 2.0/(1+exp(-2*o_a[i])) - 1.0;

    o_b[ 0] =  +1.02116392 * o_a[0] +3.48231330 * o_a[1] -8.90706866 * o_a[2]+21.32075794 * o_a[3]+24.15433800 * o_a[4] +8.93528876 * o_a[5]+38.60056683 * o_a[6] -1.60491852 * o_a[7]-36.78465064 * o_a[8]-16.46683108 * o_a[9] -8.73369463;
    o_b[ 1] =  -4.04324409 * o_a[0]+23.97768266 * o_a[1]+53.03281389 * o_a[2] -4.08040249 * o_a[3]+23.11454920 * o_a[4] -0.20477759 * o_a[5]+10.61201619 * o_a[6]+31.87957090 * o_a[7]-25.96929657 * o_a[8] +3.80818324 * o_a[9] -8.60784612;
    o_b[ 2] =  +1.03043206 * o_a[0] -7.54071542 * o_a[1]+11.52597579 * o_a[2]+19.20354406 * o_a[3]+13.79076070 * o_a[4]+10.28346702 * o_a[5] -3.87760445 * o_a[6] -1.72973591 * o_a[7] -1.56664559 * o_a[8] +2.38742395 * o_a[9] +8.31467095;
    o_b[ 3] = +11.10838082 * o_a[0]+10.24212254 * o_a[1] -0.24435575 * o_a[2] -1.65140448 * o_a[3]-18.65225743 * o_a[4]+25.35026768 * o_a[5]+13.42686467 * o_a[6]-12.22304043 * o_a[7] +1.63463961 * o_a[8] -3.92075543 * o_a[9]-18.87707917;
    o_b[ 4] =  -0.00089818 * o_a[0] -0.01657071 * o_a[1] +1.02587328 * o_a[2] +0.00066381 * o_a[3] -0.01626537 * o_a[4] -0.00393445 * o_a[5] +0.06172375 * o_a[6] -0.00063914 * o_a[7] -0.04221865 * o_a[8] +0.00203900 * o_a[9] -1.80482934;
    o_b[ 5] = -13.83576602 * o_a[0]+12.45833347 * o_a[1]+12.42817464 * o_a[2] -2.87343671 * o_a[3]-46.12634042 * o_a[4]-13.09654979 * o_a[5] +3.17254166 * o_a[6] +7.89964319 * o_a[7] +0.92267280 * o_a[8]+10.08624538 * o_a[9]+21.58382105;
    o_b[ 6] =  -0.00125984 * o_a[0] -0.03646875 * o_a[1] +1.37894206 * o_a[2] +0.00172102 * o_a[3] +0.13942651 * o_a[4] -0.00254617 * o_a[5] +0.03765085 * o_a[6] +0.00283486 * o_a[7] -0.03230421 * o_a[8] +0.00339410 * o_a[9] -0.91436705;

    for (i=0; i< 7;i++) o_b[i] = 2.0/(1+exp(-2*o_b[i])) - 1.0;

    out[ 0] =  +0.02521980 * o_b[0] -0.02298445 * o_b[1] +0.00264606 * o_b[2] +0.04326533 * o_b[3]+34.75967491 * o_b[4] +0.05333764 * o_b[5] -2.60133098 * o_b[6]+25.89448688;
    out[ 1] =  +0.00163539 * o_b[0] -0.02889589 * o_b[1] +0.01000426 * o_b[2] -0.01723471 * o_b[3]+26.36434891 * o_b[4] -0.00960361 * o_b[5]-11.65723443 * o_b[6]+21.83010873;
}

#endif       /* home_trained or montreal trained */


void dynamics_compensation(double inforcex,double inforcey,int method, double diagD)
/*  Version of the above model compensation subroutine 
    in which the computation of the force field is 
    computed before and outside of the subroutine.
    This subroutine computes the motor torque forces 
    directly. 
    The method parameter can have the following values:
     0:  no compensation
     1:  Corriolis removed
     2:  Corriolis and neural correction removed
     3:  like 2 plus dynamic compensation with diagonal mass matrix
     4:  like 2 plus replacing mass matrix by different mass matrix.

*/
{
  mat22 Jinv;
  mat22 Bq;
  mat22 Jdot;
  mat22 Jt;
  mat22 BJinv;
  mat22 Jtinv;
  mat22 Mqbarinv;

  double invgamma, det;
  double q1,q2,q1dot,q2dot;
  double cosdiff,sindiff,sinq1,sinq2,cosq1,cosq2;
  double tau1,tau2,tx,ty, tpx, tpy;
  double fhandlex,fhandley;
  double inp[10], neurout[2];

  double l1 = rob->link.s;     // length of shoulder link (=0.4064 m)
  double l3 = rob->link.e;     // length of elbow link (=0.51435 m) 
  double uu,vv,uuvv;
  double c1,c2,c3,c4,c5,c6,c7;   /* dynamic coefficients - computed below */

  double diagDinv;               // Inverse of diagonal D (isotropic inertia)
  double gain = 1.0;             // ( shut-off gain of control)


  q1 = ob->theta.s;         // robot angle 1
  q2 = ob->theta.e;         // robot angle 2

  if (ob->have_tach ==1)
    {
      q1dot =  dyncmp_var->anglevelocity.s;   // tachometer velocities  ((d/dt) theta1)
      q2dot =  dyncmp_var->anglevelocity.e;   //                        ((d/dt) theta2)
    }
  else
    {
      q1dot =  ob->fthetadot.s;   // filtered robot velocities  ((d/dt) theta1)
      q2dot =  ob->fthetadot.e;   // filtered robot velocities  ((d/dt) theta2)
    }

  sindiff = sin(q1-q2);
  cosdiff = cos(q1-q2);
  sinq1 = sin(q1);
  sinq2 = sin(q2);
  cosq1 = cos(q1);
  cosq2 = cos(q2);

/* 
The following piece of code and parameters obtained by regression
analysis may need to be changed if the robot's physical properties are
changed.
*/
  uu = l1*cosq1+l3*cosq2;
  vv = l1*sinq1+l3*sinq2+0.6;
  uuvv=uu*vv;

  c1 =   0.391162880843 + ( -0.022500130537)*uu + ( -0.027087167504)*vv + ( -0.066741726831)*uuvv;
  c2 =   0.226826719396 + (  0.010773075219)*uu + ( -0.010218495660)*vv + (  0.027345837467)*uuvv;
  c3 =   0.227888039765 + (  0.019301413084)*uu + ( -0.039404771349)*vv + (  0.236826575642)*uuvv;
  c4=0.0; c5=0.0; c6=0.0; c7=0.0;

  Bq.e00 = c1;     Bq.e01 = c2*cosdiff;
  Bq.e10 = Bq.e01; Bq.e11 = c3;

  dyncmp_var->Bofq = Bq;                                // Robot mass matrix. 

  Jinv.e00 =  -cosq2/(l1*sindiff);  Jinv.e01 =  -sinq2/(l1*sindiff);
  Jinv.e10 =  cosq1/(l3*sindiff);  Jinv.e11 = sinq1/(l3*sindiff);
  
  Jdot.e00 = -l1*cosq1*q1dot;   Jdot.e01 = -l3*cosq2*q2dot;
  Jdot.e10 = -l1*sinq1*q1dot;   Jdot.e11 = -l3*sinq2*q2dot;

  Jt.e00 = -l1*sinq1; Jt.e01 = l1*cosq1;        // J^T
  Jt.e10 = -l3*sinq2; Jt.e11 = l3*cosq2;

  BJinv = jacob2d_x_j2d(Bq,Jinv);               // This is B(q)*J^(-1)

  Jtinv.e00 = Jinv.e00; Jtinv.e11=Jinv.e11;     // J^{-T}
  Jtinv.e01 = Jinv.e10; Jtinv.e10=Jinv.e01;  
  dyncmp_var->Mofq = jacob2d_x_j2d(Jtinv, BJinv);       // M(q)  task space mass matrix.

  tpx = (Jdot.e00*q1dot + Jdot.e01*q2dot);     // term -Jdot qdot
  tpy = (Jdot.e10*q1dot + Jdot.e11*q2dot);
  dyncmp_var->Corriolis.s =  c2*sindiff*q2dot*q2dot - BJinv.e00*tpx - BJinv.e01*tpy;              // Coriolis term 
  dyncmp_var->Corriolis.e = -c2*sindiff*q1dot*q1dot - BJinv.e10*tpx - BJinv.e11*tpy; 

  inp[0]=q1; inp[1]=q2;
  inp[2]=q1dot; inp[3]=q2dot;
  inp[4]= rob->ft.dev.x;
  inp[5]= rob->ft.dev.y;
  inp[6]= rob->ft.dev.z;
  inp[7]= rob->ft.moment.x;
  inp[8]= rob->ft.moment.y;
  inp[9]= rob->ft.moment.z;
  neuralnetcorrection(inp, neurout);
  
  fhandlex = -(rob->ft.world.x);       // note: I had to invert the signs.
  fhandley = -(rob->ft.world.y);

  /* method: 
     0:  no compensation
     1:  Corriolis removed
     2:  Corriolis and neural correction removed
     3:  like 2 plus dynamic compensation with diagonal mass matrix
     4:  like 2 plus replacing mass matrix by different mass matrix.
  */
 

  switch (method)
  {
      case 0:
	  tau1 = (Jt.e00 * inforcex + Jt.e01 * inforcey);  // only force field.
	  tau2 = (Jt.e10 * inforcex + Jt.e11 * inforcey);
	  break;
	  
      case 1:                                          // correct Corriolis forces 
	  tau1 = dyncmp_var->Corriolis.s;
	  tau2 = dyncmp_var->Corriolis.e; 
	  tau1 += (Jt.e00 * inforcex + Jt.e01 * inforcey); // add force field
	  tau2 += (Jt.e10 * inforcex + Jt.e11 * inforcey);
	  break;
	  
      case 2:                                       // Corriolis forces and neural output
	  tau1 = dyncmp_var->Corriolis.s + neurout[0];
	  tau2 = dyncmp_var->Corriolis.e + neurout[1];
	  tau1 += (Jt.e00 * inforcex + Jt.e01 * inforcey);  // add force field
	  tau2 += (Jt.e10 * inforcex + Jt.e11 * inforcey);
	  break;
	  
      case 3:                                       // Corriolis, neural and inertia compensation
	  tau1 = dyncmp_var->Corriolis.s + neurout[0];
	  tau2 = dyncmp_var->Corriolis.e + neurout[1];
	  tpx = inforcex - fhandlex;                  // Force field minus handle force
	  tpy = inforcey - fhandley; 
	  diagDinv = 1.0/diagD;
	  tx = diagDinv*tpx;
	  ty = diagDinv*tpy;
	  tau1 += (BJinv.e00*tx + BJinv.e01*ty);     //  
	  tau2 += (BJinv.e10*tx + BJinv.e11*ty);     // - B J^(-1) D^(-1) h  
	  tau1 += (Jt.e00*fhandlex + Jt.e01*fhandley);
	  tau2 += (Jt.e10*fhandlex + Jt.e11*fhandley);
	  break;
	  
      case 4:                                       // Corriolis, neural correction, 
	  tau1 = dyncmp_var->Corriolis.s + neurout[0];        
	  tau2 = dyncmp_var->Corriolis.e + neurout[1];
	  tpx = inforcex - fhandlex;                  // Force field minus handle force
	  tpy = inforcey - fhandley; 
	  invgamma = 1.0/diagD;
	  // compute inverse wish mass matrix.
	  Mqbarinv.e00 = dyncmp_var->Mofq.e00 * invgamma;    
	  Mqbarinv.e01 = dyncmp_var->Mofq.e01 * invgamma;
	  Mqbarinv.e10 = dyncmp_var->Mofq.e10 * invgamma; 
	  Mqbarinv.e11 = dyncmp_var->Mofq.e11 * invgamma;
	  
	  tx = Mqbarinv.e00 * tpx +  Mqbarinv.e01 * tpy;
	  ty = Mqbarinv.e10 * tpx +  Mqbarinv.e11 * tpy;
	  tau1 += (BJinv.e00*tx + BJinv.e01*ty);     //  
	  tau2 += (BJinv.e10*tx + BJinv.e11*ty);     // - B J^(-1) Mbar(-1) h  
	  tau1 += (Jt.e00*fhandlex + Jt.e01*fhandley);
	  tau2 += (Jt.e10*fhandlex + Jt.e11*fhandley);
	  break;
	  
      case 5:                                       // Corriolis, neural correction, impose new Mass matrix.
	  tau1 = dyncmp_var->Corriolis.s + neurout[0];      // case: Mbar = gamma * M
	  tau2 = dyncmp_var->Corriolis.e + neurout[1];
	  tpx = inforcex - fhandlex;                // Force field minus handle force
	  tpy = inforcey - fhandley; 
	  // amplify the current mass matrix
	  det = dyncmp_var->Mofq.e00*dyncmp_var->Mofq.e11 - dyncmp_var->Mofq.e01*dyncmp_var->Mofq.e10;
	  invgamma = 1.0/(det*diagD);               // diagD plays the role of gamma.
	  Mqbarinv.e00 = dyncmp_var->Mofq.e11 * invgamma;    
	  Mqbarinv.e01 = -dyncmp_var->Mofq.e01 * invgamma;
	  Mqbarinv.e10 = -dyncmp_var->Mofq.e10 * invgamma; 
	  Mqbarinv.e11 = dyncmp_var->Mofq.e00 * invgamma;
	  
	  tx = Mqbarinv.e00 * tpx +  Mqbarinv.e01 * tpy;
	  ty = Mqbarinv.e10 * tpx +  Mqbarinv.e11 * tpy;
	  tau1 += (BJinv.e00*tx + BJinv.e01*ty);     //  
	  tau2 += (BJinv.e10*tx + BJinv.e11*ty);     // - B J^(-1) Mbar^(-1) h  
	  tau1 += (Jt.e00*fhandlex + Jt.e01*fhandley);
	  tau2 += (Jt.e10*fhandlex + Jt.e11*fhandley);
	  break;
	  
      default:
	  tau1=0.0;
	  tau2=0.0;
	  break;
  }
  
  tpx=dyncmp_var->Corriolis.s;
  tpy=dyncmp_var->Corriolis.e;
  dyncmp_var->Corriolis.s = Jtinv.e00 * tpx + Jtinv.e01 * tpy; 
  dyncmp_var->Corriolis.e = Jtinv.e10 * tpx + Jtinv.e11 * tpy; 
  
  ob->motor_torque.s = tau1*gain;                  // gain 0 or 1
  ob->motor_torque.e = tau2*gain;
  /* The following is doubled here for recording only, since the
     transformation of the motor torque vector into the work space 
     coordinates is not needed in the algorithm. */
  ob->motor_force.x = ob->motor_torque.s * Jinv.e00 + ob->motor_torque.e * Jinv.e10;
  ob->motor_force.y = ob->motor_torque.s * Jinv.e01 + ob->motor_torque.e * Jinv.e11;
  dyncmp_var->control_force.x = inforcex;
  dyncmp_var->control_force.y = inforcey;
  dyncmp_var->usedirectcontrol = 1; 

  // tau represents already the actual torques, 
  // so I don't do the transformation to torques.
  // instead of using dac_torque_actuator() we need to
  // use dac_direct_torque_actuator() 
  // The variable  ob->usedirectcontrol
  // is set to 1 so that in the control loop 
  // dac_direct_torque_actuator() is used. 
  // see also: write_actuators_fn()
}

