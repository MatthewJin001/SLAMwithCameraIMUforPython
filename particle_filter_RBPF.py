# -*- coding: utf-8 -*-
"""
Particle Filter
(RBPF model version)
"""

import numpy
import copy
import more_itertools
import multiprocessing
from landmark import Landmark


class ParticleFilterRBPF:

	def __init__(self):
		pass

	def setFocus(self, f_):
		self.focus = f_

	def setParameter(self, param1, param2):
		self.noise_a_sys = param1 # system noise of acceleration　加速度のシステムノイズ
		self.noise_g_sys = param2 # system noise of gyro　ジャイロのシステムノイズ


	def f_IMU(self, X, dt, dt2, accel, ori):
		""" Transition model
		- 状態方程式
			x_t = f(x_t-1, u) + w
			w ~ N(0, sigma)
		"""
	
		X_new = copy.deepcopy(X)
	
		# Transition with noise (only x,v)
		w_mean = numpy.zeros(3) # mean of noise
		w_cov_a = numpy.eye(3) * self.noise_a_sys # covariance matrix of noise (accel)
		w_a = numpy.random.multivariate_normal(w_mean, w_cov_a) # generate random
	
		X_new.x = X.x + dt*X.v + dt2*X.a + dt2*w_a
		X_new.v = X.v + dt*X.a + dt*w_a
		X_new.a = accel
		X_new.o = ori
	
		return X_new


	def f_camera(self, dt, X):
		""" Transition model
		- 状態方程式
			x_t = f(x_t-1, u) + w
			w ~ N(0, sigma)
		"""

		X_new = copy.deepcopy(X)

		dt2 = 0.5 * dt * dt

		# Transition with noise (only x,v)
		w_mean = numpy.zeros(3) # mean of noise
		w_cov_a = numpy.eye(3) * self.noise_a_sys # covariance matrix of noise (accel)
		w_a = numpy.random.multivariate_normal(w_mean, w_cov_a) # generate random

		X_new.x = X.x + dt*X.v + dt2*X.a + dt2*w_a
		X_new.v = X.v + dt*X.a + dt*w_a
		X_new.a = X.a
		X_new.o = X.o

		return X_new


	def likelihood(self, keypoints, step, P, X):
		""" Likelihood function
		- 尤度関数
			p(y|x) ~ exp(-1/2 * (|y-h(x)|.t * sigma * |y-h(x)|)
		- 観測モデル
			z = h(x) + v
			v ~ N(0, sigma)
		Parameters
		----------
		keypoints : 観測 Observation 特徴点 keypoints
		step : 現在のステップ数 current step
		x : 予測　Predicted particle
		Returns
		-------
		likelihood : 尤度 Likelihood
		"""
		
		for keypoint in keypoints:
			# The landmark is already observed or not?
			result = X.findLandmark(step-1, keypoint.index)
			if(result == "none"):
				# Fisrt observation
				# Initialize landmark and append to particle
				total = len(X.landmarks)
				landmark = Landmark(total, step, keypoint.index)
				landmark.init(X, keypoint, P, self.focus)
				X.landmarks.append(landmark)
			else:
				pass
				# Already observed
				# Kalman filter (Landmark update)
			
				# Calc likelihood
			

		return 0.0


	def resampling(self, X, W, M):
		""" Resampling
		- 等間隔サンプリング
		M : パーティクルの数 num of particles
		"""
		X_resampled = []
		Minv = 1/float(M)
		r = numpy.random.rand() * Minv
		c = W[0]
		i = 0
		for m in range(M):
			U = r + m * Minv
			while U > c:
				i += 1
				c += W[i]
			X_resampled.append(X[i])
		return X_resampled
		
	
	def predictionAndUpdate(self, X, X_predicted, weight, dt, keypoints, step, P, M):
		for i in xrange(M):
			# 推定 prediction
			X_predicted[i] = self.f_camera(dt, X[i])
			# 更新 update
			weight[i] = self.likelihood(keypoints, step, P, X_predicted[i])
			
		
	def normalizationAndResampling(self, X_predicted, weight, M):
		# 正規化 normalization of weight
		weight_sum = sum(weight) # 総和 the sum of weights
		if(weight_sum > 0.5):
			# 重みの総和が大きい（尤度が高い）場合 likelihood is high enough
			#print(weight_sum)
			# 正規化 normalization of weight
			for i in xrange(M):
				weight[i] /= weight_sum
			# リサンプリング re-sampling
			X_resampled = self.resampling(X_predicted, weight, M)
		else:
			# 重みの総和が小さい（尤度が低い）場合 likelihood is low
			#print(weight_sum),
			#print("***")
			# リサンプリングを行わない No re-sampling
			X_resampled = copy.deepcopy(X_predicted)
		return X_resampled


	def pf_step_camera(self, X, dt, keypoints, step, P, M):
		""" One Step of Sampling Importance Resampling for Particle Filter
			for IMU sensor
		Parameters
		----------
		X : 状態 List of state set
		dt : 時刻の差分 delta of time
		keypoints : 特徴点 keypoints
		step : 現在のステップ数 current step
		P : デバイス位置の分散共分散行列 Variance-covariance matrix of position
		M : パーティクルの数 num of particles
		Returns
		-------
		X_resampled : 次の状態 List updated state
		"""

		# 初期化 init
		X_predicted = range(M)
		weight = range(M)
		X_resampled = range(M)

		# 推定と更新 prediction and update
		self.predictionAndUpdate(X, X_predicted, weight, dt, keypoints, step, P, M)
		
		# 正規化とリサンプリング normalization and resampling
		X_resampled = self.normalizationAndResampling(X_predicted, weight, M)

		return X_resampled


	def pf_step_IMU(self, X, dt, accel, ori, M):
		""" One Step of Sampling Importance Resampling for Particle Filter
			for IMU sensor
		Parameters
		----------
		X : 状態 List of state set
		dt: 時刻の差分 delta of time
		accel : 制御 (加速度) Control (accel)
		ori : 制御 (姿勢) Control (orientation)
		M : パーティクルの数 num of particles
		Returns
		-------
		X_resampled : 次の状態 List updated state
		"""

		# 推定と更新 prediction and update
		# 観測がないので，パーティクルは予測だけで，更新されない
		# 予測をそのまま出力する
		dt2 = 0.5*dt*dt
		return [self.f_IMU(Xi, dt, dt2, accel, ori) for Xi in X]