"""
This tutorial introduces logistic regression using Theano and stochastic 
gradient descent.  

Logistic regression is a probabilistic, linear classifier. It is parametrized
by a weight matrix :math:`W` and a bias vector :math:`b`. Classification is
done by projecting data points onto a set of hyperplanes, the distance to
which is used to determine a class membership probability. 

Mathematically, this can be written as:

.. math::
  P(Y=i|x, W,b) &= softmax_i(W x + b) \\
                &= \frac {e^{W_i x + b_i}} {\sum_j e^{W_j x + b_j}}


The output of the model or prediction is then done by taking the argmax of 
the vector whose i'th element is P(Y=i|x).

.. math::

  y_{pred} = argmax_i P(Y=i|x,W,b)


This tutorial presents a stochastic gradient descent optimization method 
suitable for large datasets, and a conjugate gradient optimization method 
that is suitable for smaller datasets.


References:

    - textbooks: "Pattern Recognition and Machine Learning" - 
                 Christopher M. Bishop, section 4.3.2

TODO: recommended preprocessing, lr ranges, regularization ranges (explain 
      to do lr first, then add regularization)

"""
__docformat__ = 'restructedtext en'


import numpy, cPickle, gzip

import time

import theano
import theano.tensor as T

import theano.tensor.nnet


class LogisticRegression(object):
    """Multi-class Logistic Regression Class

    The logistic regression is fully described by a weight matrix :math:`W` 
    and bias vector :math:`b`. Classification is done by projecting data 
    points onto a set of hyperplanes, the distance to which is used to 
    determine a class membership probability. 
    """




    def __init__(self, input, n_in, n_out):
        """ Initialize the parameters of the logistic regression

        :param input: symbolic variable that describes the input of the 
        architecture (one minibatch)

        :param n_in: number of input units, the dimension of the space in 
        which the datapoints lie

        :param n_out: number of output units, the dimension of the space in 
        which the labels lie

        """ 

        # initialize with 0 the weights W as a matrix of shape (n_in, n_out) 
        self.W = theano.shared( value=numpy.zeros((n_in,n_out),
                                            dtype = theano.config.floatX) )
        # initialize the baises b as a vector of n_out 0s
        self.b = theano.shared( value=numpy.zeros((n_out,), 
                                            dtype = theano.config.floatX) )


        # compute vector of class-membership probabilities in symbolic form
        self.p_y_given_x = T.nnet.softmax(T.dot(input, self.W)+self.b)

        # compute prediction as class whose probability is maximal in 
        # symbolic form
        self.y_pred=T.argmax(self.p_y_given_x, axis=1)





    def negative_log_likelihood(self, y):
        """Return the negative log-likelihood of the prediction of this model
        under a given target distribution.  

        TODO : add description of the categorical_crossentropy

        :param y: corresponds to a vector that gives for each example the
        :correct label
        """
        # TODO: inline NLL formula, refer to theano function
        return T.nnet.categorical_crossentropy(self.p_y_given_x, y)





    def errors(self, y):
        """Return a float representing the number of errors in the minibatch 
        over the total number of examples of the minibatch 
        """

        # check if y has same dimension of y_pred 
        if y.ndim != self.y_pred.ndim:
            raise TypeError('y should have the same shape as self.y_pred', 
                ('y', target.type, 'y_pred', self.y_pred.type))
        # check if y is of the correct datatype        
        if y.dtype.startswith('int'):
            # the T.neq operator returns a vector of 0s and 1s, where 1
            # represents a mistake in prediction
            return T.mean(T.neq(self.y_pred, y))
        else:
            raise NotImplementedError()





def sgd_optimization_mnist( learning_rate=0.01, n_iter=100):
    """
    Demonstrate stochastic gradient descent optimization of a log-linear 
    model

    This is demonstrated on MNIST.
    
    :param learning_rate: learning rate used (factor for the stochastic 
    gradient

    :param n_iter: number of iterations ot run the optimizer 

    """

    # Load the dataset ; note that the dataset is already divided in
    # minibatches of size 10; 
    f = gzip.open('mnist.pkl.gz','rb')
    train_batches, valid_batches, test_batches = cPickle.load(f)
    f.close()

    ishape     = (28,28) # this is the size of MNIST images
    batch_size =  20     # size of the minibatch 

    # allocate symbolic variables for the data
    x = T.fmatrix()  # the data is presented as rasterized images
    y = T.lvector()  # the labels are presented as 1D vector of 
                     # [long int] labels

    # construct the logistic regression class
    classifier = LogisticRegression( \
                   input=x.reshape((batch_size,28*28)), n_in=28*28, n_out=10)

    # the cost we minimize during training is the negative log likelihood of 
    # the model in symbolic format
    cost = classifier.negative_log_likelihood(y).mean() 

    # compiling a theano function that computes the mistakes that are made by 
    # the model on a minibatch
    test_model = theano.function([x,y], classifier.errors(y))

    # compute the gradient of cost with respect to theta = (W,b) 
    g_W = T.grad(cost, classifier.W)
    g_b = T.grad(cost, classifier.b)

    # specify how to update the parameters of the model as a dictionary
    updates ={classifier.W: classifier.W - numpy.asarray(learning_rate)*g_W,\
              classifier.b: classifier.b - numpy.asarray(learning_rate)*g_b}

    # compiling a theano function `train_model` that returns the cost, but in 
    # the same time updates the parameter of the model based on the rules 
    # defined in `updates`
    train_model = theano.function([x, y], cost, updates = updates )

    # early-stopping parameters
    patience              = 5000  # look as this many examples regardless
    patience_increase     = 2     # wait this much longer when a new best is 
                                  # found
    improvement_threshold = 0.995 # a relative improvement of this much is 
                                  # considered significant
    validation_frequency  = 2500  # make this many SGD updates between 
                                  # validations

    best_params          = None
    best_validation_loss = float('inf')
    test_score           = 0.
    n_minibatches        = len(train_batches) # number of minibatchers
    start_time = time.clock()
    # have a maximum of `n_iter` iterations through the entire dataset
    for iter in xrange(n_iter* n_minibatches):

        # get epoch and minibatch index
        epoch           = iter / n_minibatches
        minibatch_index =  iter % n_minibatches

        # get the minibatches corresponding to `iter` modulo
        # `len(train_batches)`
        x,y = train_batches[ minibatch_index ]
        cost_ij = train_model(x,y)

        if (iter+1) % validation_frequency == 0: 
            # compute zero-one loss on validation set 
            this_validation_loss = 0.
            for x,y in valid_batches:
                # sum up the errors for each minibatch
                this_validation_loss += test_model(x,y)
            # get the average by dividing with the number of minibatches
            this_validation_loss /= len(valid_batches)

            print('epoch %i, minibatch %i/%i, validation error %f %%' % \
                 (epoch, minibatch_index+1,n_minibatches, \
                  this_validation_loss*100.))

            #improve patience 
            if this_validation_loss < best_validation_loss *  \
                                      improvement_threshold :
                patience = max(patience, iter * patience_increase)


            # if we got the best validation score until now
            if this_validation_loss < best_validation_loss:
                best_validation_loss = this_validation_loss
                # test it on the test set
            
                test_score = 0.
                for x,y in test_batches:
                    test_score += test_model(x,y)
                test_score /= len(test_batches)
                print(('     epoch %i, minibatch %i/%i, test error of best ' 
                       'model %f %%') % \
                  (epoch, minibatch_index+1, n_minibatches,test_score*100.))

        if patience <= iter :
                break

    end_time = time.clock()
    print(('Optimization complete with best validation score of %f %%,'
           'with test performance %f %%') %  
                 (best_validation_loss * 100., test_score*100.))
    print ('The code ran for %f minutes' % ((end_time-start_time)/60.))







if __name__ == '__main__':
    sgd_optimization_mnist()

